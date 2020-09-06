import abc
import asyncio
from typing import (
    List,
    Dict,
    Tuple,
    Mapping,
    NamedTuple,
    Any,
    Set,
    Optional,
    Iterator,
    AsyncIterator,
    Union,
)

from loguru import logger
from jsonpatch import make_patch

from .element import AbstractElement
from .events import EventHandler, EventTarget
from .utils import HasAsyncResources, async_resource, CannotAccessResource
from .hooks import LifeCycleHook


class LayoutUpdate(NamedTuple):
    """An object describing an update to a :class:`Layout`"""

    path: str
    changes: List[Dict[str, Any]]


class LayoutEvent(NamedTuple):
    target: str
    """The ID of the event handler."""
    data: List[Any]
    """A list of event data passed to the event handler."""


class ElementState(NamedTuple):
    model: Dict[str, Any]
    path: str
    element_id: int
    element_obj: AbstractElement
    event_handler_ids: Set[str]
    child_elements_ids: List[int]
    life_cycle_hook: LifeCycleHook


class Layout(HasAsyncResources):

    __slots__ = ["root", "_event_handlers"]

    if not hasattr(abc.ABC, "__weakref__"):  # pragma: no cover
        __slots__.append("__weakref__")

    def __init__(
        self, root: "AbstractElement", loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        super().__init__()
        if not isinstance(root, AbstractElement):
            raise TypeError("Expected an AbstractElement, not %r" % root)
        self.root = root
        self._event_handlers: Dict[str, EventHandler] = {}

    def update(self, element: "AbstractElement") -> None:
        try:
            self._rendering_queue.put(element)
        except CannotAccessResource:
            logger.info(f"Did not update {element} - resources of {self} are closed")

    async def dispatch(self, event: LayoutEvent) -> None:
        # It is possible for an element in the frontend to produce an event
        # associated with a backend model that has been deleted. We only handle
        # events if the element and the handler exist in the backend. Otherwise
        # we just ignore the event.
        handler = self._event_handlers.get(event.target)
        if handler is not None:
            await handler(event.data)

    async def render(self) -> LayoutUpdate:
        while True:
            element = await self._rendering_queue.get()
            if self._has_element_state(element):
                return self._create_layout_update(element)

    @async_resource
    async def _rendering_queue(self) -> AsyncIterator["_ElementQueue"]:
        queue = _ElementQueue()
        queue.put(self.root)
        yield queue

    @async_resource
    async def _element_states(self) -> AsyncIterator[Dict[int, ElementState]]:
        root_element_state = self._create_element_state(self.root, "", save=False)
        try:
            yield {root_element_state.element_id: root_element_state}
        finally:
            self._delete_element_state(root_element_state)

    def _create_layout_update(self, element: AbstractElement) -> LayoutUpdate:
        element_state = self._get_element_state(element)

        element_state.life_cycle_hook.element_will_render()

        for state in self._iter_element_states_from_root(
            element_state,
            include_root=False,
        ):
            state.life_cycle_hook.element_will_unmount()

        self._clear_element_state_event_handlers(element_state)
        self._delete_element_state_children(element_state)

        old_model = element_state.model.copy()  # we copy because it will be mutated
        new_model = self._render_element(element_state)
        changes = make_patch(old_model, new_model).patch

        for state in self._iter_element_states_from_root(
            element_state,
            include_root=True,
        ):
            state.life_cycle_hook.element_did_render()

        return LayoutUpdate(path=element_state.path, changes=changes)

    def _render_element(self, element_state: ElementState) -> Dict[str, Any]:
        try:
            element_state.life_cycle_hook.set_current()
            try:
                raw_model = element_state.element_obj.render()
            finally:
                element_state.life_cycle_hook.unset_current()

            if isinstance(raw_model, AbstractElement):
                raw_model = {"tagName": "div", "children": [raw_model]}

            resolved_model = self._render_model(element_state, raw_model)
            element_state.model.clear()
            element_state.model.update(resolved_model)
        except Exception as error:
            logger.exception(f"Failed to render {element_state.element_obj}")
            element_state.model.update({"tagName": "div", "__error__": str(error)})

        # We need to return the model from the `element_state` so that the model
        # between all `ElementState` objects within a `Layout` are shared.
        return element_state.model

    def _render_model(
        self, element_state: ElementState, model: Mapping[str, Any]
    ) -> Dict[str, Any]:
        serialized_model: Dict[str, Any] = {}
        event_handlers = self._render_model_event_targets(element_state, model)
        if event_handlers:
            serialized_model["eventHandlers"] = event_handlers
        if "children" in model:
            serialized_model["children"] = self._render_model_children(
                element_state, model["children"]
            )
        return {**model, **serialized_model}

    def _render_model_children(
        self, element_state: ElementState, children: Union[List[Any], Tuple[Any, ...]]
    ) -> List[Any]:
        resolved_children: List[Any] = []
        for index, child in enumerate(
            children if isinstance(children, (list, tuple)) else [children]
        ):
            if isinstance(child, dict):
                resolved_children.append(self._render_model(element_state, child))
            elif isinstance(child, AbstractElement):
                child_path = f"{element_state.path}/children/{index}"
                child_state = self._create_element_state(child, child_path, save=True)
                resolved_children.append(self._render_element(child_state))
                element_state.child_elements_ids.append(id(child))
            else:
                resolved_children.append(str(child))
        return resolved_children

    def _render_model_event_targets(
        self, element_state: ElementState, model: Mapping[str, Any]
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
        element_state.event_handler_ids.clear()
        element_state.event_handler_ids.update(event_handlers_by_id)
        self._event_handlers.update(event_handlers_by_id)

        return {e: h.serialize() for e, h in handlers.items()}

    def _get_element_state(self, element: AbstractElement) -> ElementState:
        return self._element_states[id(element)]

    def _has_element_state(self, element: AbstractElement) -> bool:
        return id(element) in self._element_states

    def _create_element_state(
        self,
        element: AbstractElement,
        path: str,
        save: bool,
    ) -> ElementState:
        element_id = id(element)
        state = ElementState(
            model={},
            path=path,
            element_id=element_id,
            element_obj=element,
            event_handler_ids=set(),
            child_elements_ids=[],
            life_cycle_hook=LifeCycleHook(element, self.update),
        )
        if save:
            self._element_states[element_id] = state
        return state

    def _delete_element_state(self, element_state: ElementState) -> None:
        self._clear_element_state_event_handlers(element_state)
        self._delete_element_state_children(element_state)
        del self._element_states[element_state.element_id]

    def _clear_element_state_event_handlers(self, element_state: ElementState) -> None:
        for handler_id in element_state.event_handler_ids:
            del self._event_handlers[handler_id]
        element_state.event_handler_ids.clear()

    def _delete_element_state_children(self, element_state: ElementState) -> None:
        for e_id in element_state.child_elements_ids:
            self._delete_element_state(self._element_states[e_id])
        element_state.child_elements_ids.clear()

    def _iter_element_states_from_root(
        self,
        root_element_state: ElementState,
        include_root: bool,
    ) -> Iterator[ElementState]:
        if include_root:
            pending = [root_element_state]
        else:
            pending = [
                self._element_states[i] for i in root_element_state.child_elements_ids
            ]

        while pending:
            visited_element_state = pending.pop(0)
            yield visited_element_state
            pending.extend(
                self._element_states[i]
                for i in visited_element_state.child_elements_ids
            )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.root})"


class _ElementQueue:

    __slots__ = "_queue", "_pending"

    def __init__(self) -> None:
        self._queue: "asyncio.Queue[AbstractElement]" = asyncio.Queue()
        self._pending: Set[int] = set()

    def put(self, element: AbstractElement) -> None:
        element_id = id(element)
        if element_id not in self._pending:
            self._pending.add(element_id)
            self._queue.put_nowait(element)
        return None

    async def get(self) -> AbstractElement:
        element = await self._queue.get()
        self._pending.remove(id(element))
        return element
