import abc
import asyncio
from functools import wraps
from logging import getLogger
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
)

from jsonpatch import apply_patch, make_patch

from idom.config import IDOM_DEBUG_MODE

from .component import AbstractComponent
from .events import EventHandler, EventTarget
from .hooks import LifeCycleHook
from .utils import CannotAccessResource, HasAsyncResources, async_resource
from .vdom import validate_serialized_vdom


logger = getLogger(__name__)


class LayoutUpdate(NamedTuple):
    """An object describing an update to a :class:`Layout`"""

    path: str
    changes: List[Dict[str, Any]]

    def apply_to(self, model: Any) -> Any:
        """Return the model resulting from the changes in this update"""
        return apply_patch(
            model, [{**c, "path": self.path + c["path"]} for c in self.changes]
        )

    @classmethod
    def create_from(cls, source: Any, target: Any) -> "LayoutUpdate":
        return cls("", make_patch(source, target).patch)


class LayoutEvent(NamedTuple):
    target: str
    """The ID of the event handler."""
    data: List[Any]
    """A list of event data passed to the event handler."""


class ComponentState(NamedTuple):
    model: Dict[str, Any]
    path: str
    component_id: int
    component_obj: AbstractComponent
    event_handler_ids: Set[str]
    child_component_ids: List[int]
    life_cycle_hook: LifeCycleHook


class Layout(HasAsyncResources):

    __slots__ = ["root", "_event_handlers"]

    if not hasattr(abc.ABC, "__weakref__"):  # pragma: no cover
        __slots__.append("__weakref__")

    def __init__(self, root: "AbstractComponent") -> None:
        super().__init__()
        if not isinstance(root, AbstractComponent):
            raise TypeError("Expected an AbstractComponent, not %r" % root)
        self.root = root
        self._event_handlers: Dict[str, EventHandler] = {}

    def update(self, component: "AbstractComponent") -> None:
        try:
            self._rendering_queue.put(component)
        except CannotAccessResource:
            logger.info(f"Did not update {component} - resources of {self} are closed")

    async def dispatch(self, event: LayoutEvent) -> None:
        # It is possible for an element in the frontend to produce an event
        # associated with a backend model that has been deleted. We only handle
        # events if the element and the handler exist in the backend. Otherwise
        # we just ignore the event.
        handler = self._event_handlers.get(event.target)
        if handler is not None:
            await handler(event.data)
        else:
            logger.info(
                f"Ignored event - handler {event.target!r} does not exist or its component unmounted"
            )

    async def render(self) -> LayoutUpdate:
        while True:
            component = await self._rendering_queue.get()
            if self._has_component_state(component):
                return self._create_layout_update(component)

    if IDOM_DEBUG_MODE.get():
        _debug_render = render

        @wraps(_debug_render)
        async def render(self) -> LayoutUpdate:
            # Ensure that the model is valid VDOM on each render
            result = await self._debug_render()
            validate_serialized_vdom(self._component_states[id(self.root)].model)
            return result

    @async_resource
    async def _rendering_queue(self) -> AsyncIterator["_ComponentQueue"]:
        queue = _ComponentQueue()
        queue.put(self.root)
        yield queue

    @async_resource
    async def _component_states(self) -> AsyncIterator[Dict[int, ComponentState]]:
        root_component_state = self._create_component_state(self.root, "", save=False)
        try:
            yield {root_component_state.component_id: root_component_state}
        finally:
            self._delete_component_state(root_component_state)

    def _create_layout_update(self, component: AbstractComponent) -> LayoutUpdate:
        component_state = self._get_component_state(component)

        component_state.life_cycle_hook.component_will_render()

        for state in self._iter_component_states_from_root(
            component_state,
            include_root=False,
        ):
            state.life_cycle_hook.component_will_unmount()

        self._clear_component_state_event_handlers(component_state)
        self._delete_component_state_children(component_state)

        old_model = component_state.model.copy()  # we copy because it will be mutated
        new_model = self._render_component(component_state)
        changes = make_patch(old_model, new_model).patch

        for state in self._iter_component_states_from_root(
            component_state,
            include_root=True,
        ):
            state.life_cycle_hook.component_did_render()

        return LayoutUpdate(path=component_state.path, changes=changes)

    def _render_component(self, component_state: ComponentState) -> Dict[str, Any]:
        try:
            component_state.life_cycle_hook.set_current()
            try:
                raw_model = component_state.component_obj.render()
            finally:
                component_state.life_cycle_hook.unset_current()

            if isinstance(raw_model, AbstractComponent):
                raw_model = {"tagName": "div", "children": [raw_model]}

            resolved_model = self._render_model(component_state, raw_model)
            component_state.model.clear()
            component_state.model.update(resolved_model)
        except Exception as error:
            logger.exception(f"Failed to render {component_state.component_obj}")
            component_state.model.update({"tagName": "div", "__error__": str(error)})

        # We need to return the model from the `component_state` so that the model
        # between all `ComponentState` objects within a `Layout` are shared.
        return component_state.model

    def _render_model(
        self,
        component_state: ComponentState,
        model: Mapping[str, Any],
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if path is None:
            path = component_state.path

        serialized_model: Dict[str, Any] = {}
        event_handlers = self._render_model_event_targets(component_state, model)
        if event_handlers:
            serialized_model["eventHandlers"] = event_handlers
        if "children" in model:
            serialized_model["children"] = self._render_model_children(
                component_state, model["children"], path
            )
        return {**model, **serialized_model}

    def _render_model_children(
        self,
        component_state: ComponentState,
        children: Union[List[Any], Tuple[Any, ...]],
        path: str,
    ) -> List[Any]:
        resolved_children: List[Any] = []
        for index, child in enumerate(
            children if isinstance(children, (list, tuple)) else [children]
        ):
            if isinstance(child, dict):
                child_path = f"{path}/children/{index}"
                resolved_children.append(
                    self._render_model(component_state, child, child_path)
                )
            elif isinstance(child, AbstractComponent):
                child_path = f"{path}/children/{index}"
                child_state = self._create_component_state(child, child_path, save=True)
                resolved_children.append(self._render_component(child_state))
                component_state.child_component_ids.append(id(child))
            else:
                resolved_children.append(str(child))
        return resolved_children

    def _render_model_event_targets(
        self, component_state: ComponentState, model: Mapping[str, Any]
    ) -> Dict[str, EventTarget]:
        handlers: Dict[str, EventHandler] = {}
        if "eventHandlers" in model:
            handlers.update(model["eventHandlers"])
        if "attributes" in model:
            attrs = model["attributes"]
            for k, v in list(attrs.items()):
                if callable(v):
                    if not isinstance(v, EventHandler):
                        h = handlers[k] = EventHandler()
                        h.add(attrs.pop(k))
                    else:
                        h = attrs.pop(k)
                        handlers[k] = h

        event_handlers_by_id = {h.id: h for h in handlers.values()}
        component_state.event_handler_ids.clear()
        component_state.event_handler_ids.update(event_handlers_by_id)
        self._event_handlers.update(event_handlers_by_id)

        return {e: h.serialize() for e, h in handlers.items()}

    def _get_component_state(self, component: AbstractComponent) -> ComponentState:
        return self._component_states[id(component)]

    def _has_component_state(self, component: AbstractComponent) -> bool:
        return id(component) in self._component_states

    def _create_component_state(
        self,
        component: AbstractComponent,
        path: str,
        save: bool,
    ) -> ComponentState:
        component_id = id(component)
        state = ComponentState(
            model={},
            path=path,
            component_id=component_id,
            component_obj=component,
            event_handler_ids=set(),
            child_component_ids=[],
            life_cycle_hook=LifeCycleHook(component, self.update),
        )
        if save:
            self._component_states[component_id] = state
        return state

    def _delete_component_state(self, component_state: ComponentState) -> None:
        self._clear_component_state_event_handlers(component_state)
        self._delete_component_state_children(component_state)
        del self._component_states[component_state.component_id]

    def _clear_component_state_event_handlers(
        self, component_state: ComponentState
    ) -> None:
        for handler_id in component_state.event_handler_ids:
            del self._event_handlers[handler_id]
        component_state.event_handler_ids.clear()

    def _delete_component_state_children(self, component_state: ComponentState) -> None:
        for e_id in component_state.child_component_ids:
            self._delete_component_state(self._component_states[e_id])
        component_state.child_component_ids.clear()

    def _iter_component_states_from_root(
        self,
        root_component_state: ComponentState,
        include_root: bool,
    ) -> Iterator[ComponentState]:
        if include_root:
            pending = [root_component_state]
        else:
            pending = [
                self._component_states[i]
                for i in root_component_state.child_component_ids
            ]

        while pending:
            visited_component_state = pending.pop(0)
            yield visited_component_state
            pending.extend(
                self._component_states[i]
                for i in visited_component_state.child_component_ids
            )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.root})"


class _ComponentQueue:

    __slots__ = "_loop", "_queue", "_pending"

    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()
        self._queue: "asyncio.Queue[AbstractComponent]" = asyncio.Queue()
        self._pending: Set[int] = set()

    def put(self, component: AbstractComponent) -> None:
        component_id = id(component)
        if component_id not in self._pending:
            self._pending.add(component_id)
            self._loop.call_soon_threadsafe(self._queue.put_nowait, component)
        return None

    async def get(self) -> AbstractComponent:
        component = await self._queue.get()
        self._pending.remove(id(component))
        return component
