from __future__ import annotations

import abc
import asyncio
from collections import Counter
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
from weakref import ref

from jsonpatch import apply_patch, make_patch
from typing_extensions import TypedDict

from idom.config import IDOM_DEBUG_MODE, IDOM_FEATURE_INDEX_AS_DEFAULT_KEY

from .component import AbstractComponent
from .events import EventHandler
from .hooks import LifeCycleHook
from .utils import CannotAccessResource, HasAsyncResources, async_resource, hex_id
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
        new_state = old_state.new(None, component)

        self._render_component(old_state, new_state, component)
        changes = make_patch(getattr(old_state, "model", {}), new_state.model).patch

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

        if old_state is not None and old_state.component is not component:
            del self._model_state_by_component_id[id(old_state.component)]
        self._model_state_by_component_id[id(component)] = new_state

        try:
            parent = new_state.parent
        except AttributeError:
            pass
        else:
            key, index = new_state.key, new_state.index
            if old_state is not None:
                assert (key, index) == (old_state.key, old_state.index,), (
                    "state mismatch during component update - "
                    f"key {key!r}!={old_state.key} "
                    f"or index {index}!={old_state.index}"
                )
            parent.children_by_key[key] = new_state
            # need to do insertion in case where old_state is None and we're appending
            parent.model["children"][index : index + 1] = [new_state.model]

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

        if old_state is None:
            self._render_model_event_handlers_without_old_state(
                new_state, handlers_by_event
            )
            return None

        for old_event in set(old_state.targets_by_event).difference(handlers_by_event):
            old_target = old_state.targets_by_event[old_event]
            del self._event_handlers[old_target]

        if not handlers_by_event:
            return None

        model_event_handlers = new_state.model["eventHandlers"] = {}
        for event, handler in handlers_by_event.items():
            target = old_state.targets_by_event.get(event, hex_id(handler))
            new_state.targets_by_event[event] = target
            self._event_handlers[target] = handler
            model_event_handlers[event] = {
                "target": target,
                "preventDefault": handler.prevent_default,
                "stopPropagation": handler.stop_propagation,
            }

        return None

    def _render_model_event_handlers_without_old_state(
        self,
        new_state: _ModelState,
        handlers_by_event: Dict[str, EventHandler],
    ) -> None:
        if not handlers_by_event:
            return None

        model_event_handlers = new_state.model["eventHandlers"] = {}
        for event, handler in handlers_by_event.items():
            target = hex_id(handler)
            new_state.targets_by_event[event] = target
            self._event_handlers[target] = handler
            model_event_handlers[event] = {
                "target": target,
                "preventDefault": handler.prevent_default,
                "stopPropagation": handler.stop_propagation,
            }

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

        child_type_key_tuples = list(_process_child_type_and_key(raw_children))

        new_keys = {item[2] for item in child_type_key_tuples}
        if len(new_keys) != len(raw_children):
            key_counter = Counter(item[2] for item in child_type_key_tuples)
            duplicate_keys = [key for key, count in key_counter.items() if count > 1]
            raise ValueError(
                f"Duplicate keys {duplicate_keys} at {new_state.patch_path or '/'!r}"
            )

        old_keys = set(old_state.children_by_key).difference(new_keys)
        if old_keys:
            self._unmount_model_states(
                [old_state.children_by_key[key] for key in old_keys]
            )

        new_children = new_state.model["children"] = []
        for index, (child, child_type, key) in enumerate(child_type_key_tuples):
            if child_type is _DICT_TYPE:
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is not None:
                    new_child_state = old_child_state.new(new_state, None)
                else:
                    new_child_state = _ModelState(new_state, index, key, None)
                self._render_model(old_child_state, new_child_state, child)
                new_children.append(new_child_state.model)
                new_state.children_by_key[key] = new_child_state
            elif child_type is _COMPONENT_TYPE:
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is not None:
                    new_child_state = old_child_state.new(new_state, child)
                else:
                    hook = LifeCycleHook(child, self)
                    new_child_state = _ModelState(new_state, index, key, hook)
                self._render_component(old_child_state, new_child_state, child)
            else:
                new_children.append(child)

    def _render_model_children_without_old_state(
        self, new_state: _ModelState, raw_children: List[Any]
    ) -> None:
        new_children = new_state.model["children"] = []
        for index, (child, child_type, key) in enumerate(
            _process_child_type_and_key(raw_children)
        ):
            if child_type is _DICT_TYPE:
                child_state = _ModelState(new_state, index, key, None)
                self._render_model(None, child_state, child)
                new_children.append(child_state.model)
                new_state.children_by_key[key] = child_state
            elif child_type is _COMPONENT_TYPE:
                life_cycle_hook = LifeCycleHook(child, self)
                child_state = _ModelState(new_state, index, key, life_cycle_hook)
                self._render_component(None, child_state, child)
            else:
                new_children.append(child)

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
        "_parent_ref",
        "life_cycle_hook",
        "component",
        "patch_path",
        "model",
        "targets_by_event",
        "children_by_key",
        "__weakref__",
    )

    model: _ModelVdom
    life_cycle_hook: LifeCycleHook
    patch_path: str
    component: AbstractComponent

    def __init__(
        self,
        parent: Optional[_ModelState],
        index: int,
        key: Any,
        life_cycle_hook: Optional[LifeCycleHook],
    ) -> None:
        self.index = index
        self.key = key

        if parent is not None:
            self._parent_ref = ref(parent)
            self.patch_path = f"{parent.patch_path}/children/{index}"
        else:
            self.patch_path = ""

        if life_cycle_hook is not None:
            self.life_cycle_hook = life_cycle_hook
            self.component = life_cycle_hook.component

        self.targets_by_event: Dict[str, str] = {}
        self.children_by_key: Dict[str, _ModelState] = {}

    @property
    def parent(self) -> _ModelState:
        # An AttributeError here is ok. It's synonymous
        # with the existance of 'parent' attribute
        p = self._parent_ref()
        assert p is not None, "detached model state"
        return p

    def new(
        self,
        new_parent: Optional[_ModelState],
        component: Optional[AbstractComponent],
    ) -> _ModelState:
        if new_parent is None:
            new_parent = getattr(self, "parent", None)

        life_cycle_hook: Optional[LifeCycleHook]
        if hasattr(self, "life_cycle_hook"):
            assert component is not None
            life_cycle_hook = self.life_cycle_hook
            life_cycle_hook.component = component
        else:
            life_cycle_hook = None

        return _ModelState(new_parent, self.index, self.key, life_cycle_hook)

    def iter_children(self, include_self: bool = True) -> Iterator[_ModelState]:
        to_yield = [self] if include_self else []
        while to_yield:
            node = to_yield.pop()
            yield node
            to_yield.extend(node.children_by_key.values())


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


def _process_child_type_and_key(
    children: List[Any],
) -> Iterator[Tuple[Any, int, Any]]:
    for index, child in enumerate(children):
        if isinstance(child, dict):
            child_type = _DICT_TYPE
            key = child.get("key")
        elif isinstance(child, AbstractComponent):
            child_type = _COMPONENT_TYPE
            key = getattr(child, "key", None)
        else:
            child = f"{child}"
            child_type = _STRING_TYPE
            key = None

        if key is None:
            key = _default_key(index)

        yield (child, child_type, key)


if IDOM_FEATURE_INDEX_AS_DEFAULT_KEY.get():

    def _default_key(index: int) -> Any:  # pragma: no cover
        return index


else:

    def _default_key(index: int) -> Any:
        return object()


# used in _process_child_type_and_key
_DICT_TYPE = 1
_COMPONENT_TYPE = 2
_STRING_TYPE = 3


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
