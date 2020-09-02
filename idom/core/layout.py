import abc
import asyncio
from types import coroutine
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
from .events import EventHandler
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
    path: List[int]
    element_obj: AbstractElement
    event_handler_ids: Set[str]
    child_elements_ids: List[str]
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

    async def render(self) -> Dict[str, Any]:
        while True:
            element = await self._rendering_queue.get()
            if element.id in self._element_states:
                return await self._create_layout_update(element)

    @async_resource
    async def _rendering_queue(self) -> AsyncIterator["_ElementQueue"]:
        queue = _ElementQueue()
        queue.put(self.root)
        yield queue

    @async_resource
    async def _element_states(self) -> AsyncIterator[ElementState]:
        root_element_state = self._create_element_state(self.root, "")
        try:
            yield {self.root.id: root_element_state}
        finally:
            self._delete_element_state(root_element_state)

    async def _create_layout_update(self, element: AbstractElement) -> LayoutUpdate:
        element_state = self._element_states[element.id]

        element_state.life_cycle_hook.element_will_render()

        for state in self._iter_element_states_from_root(
            element_state,
            include_root=False,
        ):
            state.life_cycle_hook.element_will_unmount()

        self._clear_element_state_event_handlers(element_state)
        self._delete_element_state_children(element_state)

        old_model = element_state.model.copy()  # we copy because it will be mutated
        new_model = await self._render_element(element_state)
        changes = make_patch(old_model, new_model).patch

        for state in self._iter_element_states_from_root(
            element_state,
            include_root=True,
        ):
            state.life_cycle_hook.element_did_render()

        return LayoutUpdate(path=element_state.path, changes=changes)

    async def _render_element(self, element_state: ElementState) -> Dict[str, Any]:
        try:
            # BUG: https://github.com/python/mypy/issues/9256
            raw_model = await _render_with_life_cycle_hook(element_state)  # type: ignore

            if isinstance(raw_model, AbstractElement):
                raw_model = {"tagName": "div", "children": [raw_model]}

            resolved_model = await self._render_model(element_state, raw_model)
            element_state.model.clear()
            element_state.model.update(resolved_model)
        except Exception:
            logger.exception(f"Failed to render {element_state.element_obj}")

        # We need to return the model from the `element_state` so that the model
        # between all `ElementState` objects within a `Layout` are shared.
        return element_state.model

    async def _render_model(
        self, element_state: ElementState, model: Mapping[str, Any]
    ) -> Dict[str, Any]:
        model: Dict[str, Any] = dict(model)

        model["eventHandlers"] = self._render_model_event_handlers(element_state, model)

        if "children" in model:
            model["children"] = await self._render_model_children(
                element_state, model["children"]
            )

        return model

    async def _render_model_children(
        self, element_state: ElementState, children: Union[List[Any], Tuple[Any, ...]]
    ) -> List[Any]:
        resolved_children: List[Any] = []
        for index, child in enumerate(
            children if isinstance(children, (list, tuple)) else [children]
        ):
            if isinstance(child, Mapping):
                resolved_children.append(await self._render_model(element_state, child))
            elif isinstance(child, AbstractElement):
                child_path = f"{element_state.path}/children/{index}"
                child_state = self._create_element_state(child, child_path)
                self._element_states[child.id] = child_state
                resolved_children.append(await self._render_element(child_state))
                element_state.child_elements_ids.append(child.id)
            else:
                resolved_children.append(str(child))
        return resolved_children

    def _render_model_event_handlers(
        self, element_state: ElementState, model: Mapping[str, Any]
    ) -> Dict[str, str]:
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

    def _create_element_state(
        self, element: AbstractElement, path: str
    ) -> ElementState:
        return ElementState(
            model={},
            path=path,
            element_obj=element,
            event_handler_ids=set(),
            child_elements_ids=[],
            life_cycle_hook=LifeCycleHook(element, self.update),
        )

    def _reset_element_state(self, element_state: ElementState) -> None:
        self._clear_element_state_event_handlers(element_state)
        self._delete_element_state_children(element_state)

    def _delete_element_state(self, element_state: ElementState) -> None:
        self._clear_element_state_event_handlers(element_state)
        self._delete_element_state_children(element_state)
        del self._element_states[element_state.element_obj.id]

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


@coroutine
def _render_with_life_cycle_hook(element_state: ElementState) -> Iterator[None]:
    """Render an element which may use hooks.

    We use a coroutine here because we need to know when control is yielded
    back to the event loop since it might switch to render a different element.
    """
    gen = element_state.element_obj.render().__await__()
    try:
        while True:
            element_state.life_cycle_hook.set_current()
            value = next(gen)
            element_state.life_cycle_hook.unset_current()
            yield value
    except StopIteration as error:
        return error.value
    finally:
        element_state.life_cycle_hook.unset_current()


class _ElementQueue:

    __slots__ = "_queue", "_pending"

    def __init__(self):
        self._queue = asyncio.Queue()
        self._pending = set()

    def put(self, element: AbstractElement) -> None:
        if element.id not in self._pending:
            self._pending.add(element.id)
            self._queue.put_nowait(element)
        return None

    async def get(self) -> AbstractElement:
        element = await self._queue.get()
        self._pending.remove(element.id)
        return element
