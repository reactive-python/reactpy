from __future__ import annotations

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
    NamedTuple,
    Optional,
    Set,
    Tuple,
)
from weakref import ReferenceType, ref

from jsonpatch import apply_patch, make_patch
from typing_extensions import TypedDict

from idom.config import IDOM_DEBUG_MODE

from .component import AbstractComponent
from .events import EventHandler
from .hooks import LifeCycleHook
from .utils import CannotAccessResource, HasAsyncResources, async_resource
from .vdom import validate_vdom


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
            if id(component) in self._model_state_by_component_id:
                return self._create_layout_update(component)

    if IDOM_DEBUG_MODE.get():
        # If in debug mode inject a function that ensures all returned updates
        # contain valid VDOM models. We only do this in debug mode in order to
        # avoid unnecessarily impacting performance.

        _debug_render = render

        @wraps(_debug_render)
        async def render(self) -> LayoutUpdate:
            # Ensure that the model is valid VDOM on each render
            result = await self._debug_render()
            validate_vdom(self._model_state_by_component_id[id(self.root)].model)
            return result

    @async_resource
    async def _rendering_queue(self) -> AsyncIterator[_ComponentQueue]:
        queue = _ComponentQueue()
        queue.put(self.root)
        yield queue

    @async_resource
    async def _model_state_by_component_id(
        self,
    ) -> AsyncIterator[Dict[int, _ModelState]]:
        root_state = _ModelState(None, -1, "", LifeCycleHook(self.root, self))
        yield {id(self.root): root_state}
        self._unmount_model_states([root_state])

    def _create_layout_update(self, component: AbstractComponent) -> LayoutUpdate:
        old_state = self._model_state_by_component_id[id(component)]
        new_state = old_state.new()

        self._render_component(old_state, new_state, component)
        changes = make_patch(getattr(old_state, "model", {}), new_state.model).patch

        # replace model and state in parent
        if hasattr(new_state, "parent_ref"):
            parent = new_state.parent_ref()
            if parent is not None:
                parent.children_by_key[new_state.key] = new_state
                parent.model["children"][new_state.index] = new_state.model

        # replace in global state
        self._model_state_by_component_id[id(component)] = new_state

        # hook effects must run after the update is complete
        for state in new_state.iter_children():
            if hasattr(state, "life_cycle_hook"):
                state.life_cycle_hook.component_did_render()

        return LayoutUpdate(path=new_state.patch_path, changes=changes)

    def _render_component(
        self,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        component: AbstractComponent,
    ) -> None:
        life_cycle_hook = new_state.life_cycle_hook
        life_cycle_hook.component_will_render()
        try:
            life_cycle_hook.set_current()
            try:
                raw_model = component.render()
            finally:
                life_cycle_hook.unset_current()
            self._render_model(old_state, new_state, raw_model)
        except Exception as error:
            logger.exception(f"Failed to render {component}")
            new_state.model = {"tagName": "__error__", "children": [str(error)]}

    def _render_model(
        self,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        raw_model: Any,
    ) -> None:
        new_state.model = {"tagName": raw_model["tagName"]}

        self._render_model_attributes(old_state, new_state, raw_model)
        self._render_model_children(old_state, new_state, raw_model.get("children", []))

        if "key" in raw_model:
            new_state.model["key"] = raw_model["key"]
        if "importSource" in raw_model:
            new_state.model["importSource"] = raw_model["importSource"]

    def _render_model_attributes(
        self,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        raw_model: Dict[str, Any],
    ) -> None:
        # extract event handlers from 'eventHandlers' and 'attributes'
        handlers_by_event: Dict[str, EventHandler] = {}

        if "eventHandlers" in raw_model:
            handlers_by_event.update(raw_model["eventHandlers"])

        if "attributes" in raw_model:
            attrs = new_state.model["attributes"] = raw_model["attributes"].copy()
            for k, v in list(attrs.items()):
                if callable(v):
                    if not isinstance(v, EventHandler):
                        h = handlers_by_event[k] = EventHandler()
                        h.add(attrs.pop(k))
                    else:
                        h = attrs.pop(k)
                        handlers_by_event[k] = h

        handlers_by_target: Dict[str, EventHandler] = {}
        model_event_targets: Dict[str, _ModelEventTarget] = {}
        for event, handler in handlers_by_event.items():
            target = f"{new_state.key_path}/{event}"
            handlers_by_target[target] = handler
            model_event_targets[event] = {
                "target": target,
                "preventDefault": handler.prevent_default,
                "stopPropagation": handler.stop_propagation,
            }

        if old_state is not None:
            for old_target in set(old_state.event_targets).difference(
                handlers_by_target
            ):
                del self._event_handlers[old_target]

        if model_event_targets:
            new_state.event_targets.update(handlers_by_target)
            self._event_handlers.update(handlers_by_target)
            new_state.model["eventHandlers"] = model_event_targets

        return None

    def _render_model_children(
        self,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        raw_children: Any,
    ) -> None:
        if not isinstance(raw_children, (list, tuple)):
            raw_children = [raw_children]

        if old_state is None:
            if raw_children:
                self._render_model_children_without_old_state(new_state, raw_children)
            return None
        elif not raw_children:
            self._unmount_model_states(list(old_state.children_by_key.values()))
            return None

        DICT_TYPE, COMPONENT_TYPE, STRING_TYPE = 1, 2, 3  # noqa

        raw_typed_children_by_key: Dict[str, Tuple[int, Any]] = {}
        for index, child in enumerate(raw_children):
            if isinstance(child, dict):
                child_type = DICT_TYPE
                key = child.get("key") or hex(id(child))[2:]
            elif isinstance(child, AbstractComponent):
                child_type = COMPONENT_TYPE
                key = getattr(child, "key", "") or hex(id(child))[2:]
            else:
                child = str(child)
                child_type = STRING_TYPE
                # The key doesn't matter since we won't look it up - all that matter is
                # that the key is unique (which this approach guarantees)
                key = object()
            raw_typed_children_by_key[key] = (child_type, child)

        if len(raw_typed_children_by_key) != len(raw_children):
            raise ValueError(f"Duplicate keys in {raw_children}")

        old_keys = set(old_state.children_by_key).difference(raw_typed_children_by_key)
        old_child_states = {key: old_state.children_by_key[key] for key in old_keys}
        if old_child_states:
            self._unmount_model_states(list(old_child_states.values()))

        new_children = new_state.model["children"] = []
        for index, (key, (child_type, child)) in enumerate(
            raw_typed_children_by_key.items()
        ):
            if child_type is DICT_TYPE:
                child_state = _ModelState(ref(new_state), index, key, None)
                self._render_model(old_child_states.get(key), child_state, child)
                new_children.append(child_state.model)
                new_state.children_by_key[key] = child_state
            elif child_type is COMPONENT_TYPE:
                key = getattr(child, "key", "") or hex(id(child))
                life_cycle_hook = LifeCycleHook(child, self)
                child_state = _ModelState(ref(new_state), index, key, life_cycle_hook)
                self._render_component(old_child_states.get(key), child_state, child)
                new_children.append(child_state.model)
                new_state.children_by_key[key] = child_state
                self._model_state_by_component_id[id(child)] = child_state
            else:
                new_children.append(child)

    def _render_model_children_without_old_state(
        self, new_state: _ModelState, raw_children: List[Any]
    ) -> None:
        new_children = new_state.model["children"] = []
        for index, child in enumerate(raw_children):
            if isinstance(child, dict):
                key = child.get("key") or hex(id(child))
                child_state = _ModelState(ref(new_state), index, key, None)
                self._render_model(None, child_state, child)
                new_children.append(child_state.model)
                new_state.children_by_key[key] = child_state
            elif isinstance(child, AbstractComponent):
                key = getattr(child, "key", "") or hex(id(child))
                life_cycle_hook = LifeCycleHook(child, self)
                child_state = _ModelState(ref(new_state), index, key, life_cycle_hook)
                self._render_component(None, child_state, child)
                new_children.append(child_state.model)
                new_state.children_by_key[key] = child_state
                self._model_state_by_component_id[id(child)] = child_state
            else:
                new_children.append(str(child))

    def _unmount_model_states(self, old_states: List[_ModelState]) -> None:
        to_unmount = old_states[::-1]
        while to_unmount:
            state = to_unmount.pop()
            if hasattr(state, "life_cycle_hook"):
                hook = state.life_cycle_hook
                hook.component_will_unmount()
                del self._model_state_by_component_id[id(hook.component)]
            to_unmount.extend(state.children_by_key.values())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.root})"


class _ModelState:

    __slots__ = (
        "index",
        "key",
        "parent_ref",
        "life_cycle_hook",
        "patch_path",
        "key_path",
        "model",
        "event_targets",
        "children_by_key",
        "__weakref__",
    )

    model: _ModelVdom

    def __init__(
        self,
        parent_ref: Optional[ReferenceType[_ModelState]],
        index: int,
        key: str,
        life_cycle_hook: Optional[LifeCycleHook],
    ) -> None:
        self.index = index
        self.key = key

        if parent_ref is not None:
            self.parent_ref = parent_ref
            # temporarilly hydrate for use below
            parent = parent_ref()
        else:
            parent = None

        if life_cycle_hook is not None:
            self.life_cycle_hook = life_cycle_hook

        if parent is None:
            self.key_path = self.patch_path = ""
        else:
            self.key_path = f"{parent.key_path}/{key}"
            self.patch_path = f"{parent.patch_path}/children/{index}"

        self.event_targets: Set[str] = set()
        self.children_by_key: Dict[str, _ModelState] = {}

    def new(self) -> _ModelState:
        return _ModelState(
            getattr(self, "parent_ref", None),
            self.index,
            self.key,
            getattr(self, "life_cycle_hook", None),
        )

    def iter_children(self, include_self: bool = True) -> Iterator[_ModelState]:
        to_yield = [self] if include_self else []
        while to_yield:
            node = to_yield.pop()
            yield node
            to_yield.extend(node.children_by_key.values())


class _ModelEventTarget(TypedDict):
    target: str
    preventDefault: bool  # noqa
    stopPropagation: bool  # noqa


class _ModelImportSource(TypedDict):
    source: str
    fallback: Any


class _ModelVdomOptional(TypedDict, total=False):
    key: str  # noqa
    children: List[Any]  # noqa
    attributes: Dict[str, Any]  # noqa
    eventHandlers: Dict[str, _ModelEventTarget]  # noqa
    importSource: _ModelImportSource  # noqa


class _ModelVdomRequired(TypedDict, total=True):
    tagName: str  # noqa


class _ModelVdom(_ModelVdomRequired, _ModelVdomOptional):
    """A VDOM dictionary model specifically for use with a :class:`Layout`"""


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
