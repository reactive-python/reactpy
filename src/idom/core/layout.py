from __future__ import annotations

import abc
import asyncio
from collections import Counter
from contextlib import ExitStack
from logging import getLogger
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    NamedTuple,
    NewType,
    Optional,
    Set,
    Tuple,
    TypeVar,
    cast,
)
from uuid import uuid4
from weakref import ref as weakref

from idom.config import IDOM_CHECK_VDOM_SPEC, IDOM_DEBUG_MODE
from idom.utils import Ref

from ._event_proxy import _wrap_in_warning_event_proxies
from .hooks import LifeCycleHook
from .types import ComponentType, EventHandlerDict, VdomDict, VdomJson
from .vdom import validate_vdom_json


logger = getLogger(__name__)


class LayoutUpdate(NamedTuple):
    """A change to a view as a result of a :meth:`Layout.render`"""

    path: str
    """A "/" delimited path to the element from the root of the layout"""

    old: Optional[VdomJson]
    """The old state of the layout"""

    new: VdomJson
    """The new state of the layout"""


class LayoutEvent(NamedTuple):
    """An event that should be relayed to its handler by :meth:`Layout.deliver`"""

    target: str
    """The ID of the event handler."""
    data: List[Any]
    """A list of event data passed to the event handler."""


class Layout:
    """Responsible for "rendering" components. That is, turning them into VDOM."""

    __slots__ = [
        "root",
        "_event_handlers",
        "_rendering_queue",
        "_root_life_cycle_state_id",
        "_model_states_by_life_cycle_state_id",
    ]

    if not hasattr(abc.ABC, "__weakref__"):  # pragma: no cover
        __slots__.append("__weakref__")

    def __init__(self, root: "ComponentType") -> None:
        super().__init__()
        if not isinstance(root, ComponentType):
            raise TypeError(f"Expected a ComponentType, not {type(root)!r}.")
        self.root = root

    async def __aenter__(self) -> Layout:
        # create attributes here to avoid access before entering context manager
        self._event_handlers: EventHandlerDict = {}

        self._rendering_queue: _ThreadSafeQueue[_LifeCycleStateId] = _ThreadSafeQueue()
        root_model_state = _new_root_model_state(self.root, self._rendering_queue.put)

        self._root_life_cycle_state_id = root_id = root_model_state.life_cycle_state.id
        self._rendering_queue.put(root_id)

        self._model_states_by_life_cycle_state_id = {root_id: root_model_state}

        return self

    async def __aexit__(self, *exc: Any) -> None:
        root_csid = self._root_life_cycle_state_id
        root_model_state = self._model_states_by_life_cycle_state_id[root_csid]
        self._unmount_model_states([root_model_state])

        # delete attributes here to avoid access after exiting context manager
        del self._event_handlers
        del self._rendering_queue
        del self._root_life_cycle_state_id
        del self._model_states_by_life_cycle_state_id

        return None

    async def deliver(self, event: LayoutEvent) -> None:
        """Dispatch an event to the targeted handler"""
        # It is possible for an element in the frontend to produce an event
        # associated with a backend model that has been deleted. We only handle
        # events if the element and the handler exist in the backend. Otherwise
        # we just ignore the event.
        handler = self._event_handlers.get(event.target)

        if handler is not None:
            try:
                await handler.function(_wrap_in_warning_event_proxies(event.data))
            except Exception:
                logger.exception(f"Failed to execute event handler {handler}")
        else:
            logger.info(
                f"Ignored event - handler {event.target!r} does not exist or its component unmounted"
            )

    async def render(self) -> LayoutUpdate:
        """Await the next available render. This will block until a component is updated"""
        while True:
            model_state_id = await self._rendering_queue.get()
            try:
                model_state = self._model_states_by_life_cycle_state_id[model_state_id]
            except KeyError:
                logger.debug(
                    "Did not render component with model state ID "
                    f"{model_state_id!r} - component already unmounted"
                )
            else:
                update = self._create_layout_update(model_state)
                if IDOM_CHECK_VDOM_SPEC.current:
                    root_id = self._root_life_cycle_state_id
                    root_model = self._model_states_by_life_cycle_state_id[root_id]
                    validate_vdom_json(root_model.model.current)
                return update

    def _create_layout_update(self, old_state: _ModelState) -> LayoutUpdate:
        new_state = _copy_component_model_state(old_state)
        component = new_state.life_cycle_state.component

        with ExitStack() as exit_stack:
            self._render_component(exit_stack, old_state, new_state, component)

        old_model: Optional[VdomJson]
        try:
            old_model = old_state.model.current
        except AttributeError:
            old_model = None

        return LayoutUpdate(
            path=new_state.patch_path,
            old=old_model,
            new=new_state.model.current,
        )

    def _render_component(
        self,
        exit_stack: ExitStack,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        component: ComponentType,
    ) -> None:
        life_cycle_state = new_state.life_cycle_state
        self._model_states_by_life_cycle_state_id[life_cycle_state.id] = new_state

        if (
            old_state is not None
            and hasattr(old_state.model, "current")
            and old_state.is_component_state
            and not _check_should_render(
                old_state.life_cycle_state.component, component
            )
        ):
            new_state.model.current = old_state.model.current
        else:
            life_cycle_hook = life_cycle_state.hook
            life_cycle_hook.affect_component_will_render(component)
            exit_stack.callback(life_cycle_hook.affect_layout_did_render)
            life_cycle_hook.set_current()
            try:
                raw_model = component.render()
                # wrap the model in a fragment (i.e. tagName="") to ensure components have
                # a separate node in the model state tree. This could be removed if this
                # components are given a node in the tree some other way
                wrapper_model: VdomDict = {"tagName": ""}
                if raw_model is not None:
                    wrapper_model["children"] = [raw_model]
                self._render_model(exit_stack, old_state, new_state, wrapper_model)
            except Exception as error:
                logger.exception(f"Failed to render {component}")
                new_state.model.current = {
                    "tagName": "",
                    "error": (
                        f"{type(error).__name__}: {error}"
                        if IDOM_DEBUG_MODE.current
                        else ""
                    ),
                }
            finally:
                life_cycle_hook.unset_current()
                life_cycle_hook.affect_component_did_render()

        try:
            parent = new_state.parent
        except AttributeError:
            pass  # only happens for root component
        else:
            key, index = new_state.key, new_state.index
            parent.children_by_key[key] = new_state
            # need to add this model to parent's children without mutating parent model
            old_parent_model = parent.model.current
            old_parent_children = old_parent_model["children"]
            parent.model.current = {
                **old_parent_model,  # type: ignore[misc]
                "children": [
                    *old_parent_children[:index],
                    new_state.model.current,
                    *old_parent_children[index + 1 :],
                ],
            }
        finally:
            # avoid double render
            self._rendering_queue.remove_if_pending(life_cycle_state.id)

    def _render_model(
        self,
        exit_stack: ExitStack,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        raw_model: Any,
    ) -> None:
        new_state.model.current = {"tagName": raw_model["tagName"]}
        if "key" in raw_model:
            new_state.key = new_state.model.current["key"] = raw_model["key"]
        if "importSource" in raw_model:
            new_state.model.current["importSource"] = raw_model["importSource"]
        self._render_model_attributes(old_state, new_state, raw_model)
        self._render_model_children(
            exit_stack, old_state, new_state, raw_model.get("children", [])
        )

    def _render_model_attributes(
        self,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        raw_model: Dict[str, Any],
    ) -> None:
        # extract event handlers from 'eventHandlers' and 'attributes'
        handlers_by_event: EventHandlerDict = raw_model.get("eventHandlers", {})

        if "attributes" in raw_model:
            attrs = raw_model["attributes"].copy()
            new_state.model.current["attributes"] = attrs

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

        model_event_handlers = new_state.model.current["eventHandlers"] = {}
        for event, handler in handlers_by_event.items():
            if event in old_state.targets_by_event:
                target = old_state.targets_by_event[event]
            else:
                target = uuid4().hex if handler.target is None else handler.target
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
        handlers_by_event: EventHandlerDict,
    ) -> None:
        if not handlers_by_event:
            return None

        model_event_handlers = new_state.model.current["eventHandlers"] = {}
        for event, handler in handlers_by_event.items():
            target = uuid4().hex if handler.target is None else handler.target
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
        exit_stack: ExitStack,
        old_state: Optional[_ModelState],
        new_state: _ModelState,
        raw_children: Any,
    ) -> None:
        if not isinstance(raw_children, (list, tuple)):
            raw_children = [raw_children]

        if old_state is None:
            if raw_children:
                self._render_model_children_without_old_state(
                    exit_stack, new_state, raw_children
                )
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

        new_state.model.current["children"] = []
        for index, (child, child_type, key) in enumerate(child_type_key_tuples):
            old_child_state = old_state.children_by_key.get(key)
            if child_type is _DICT_TYPE:
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is None:
                    new_child_state = _make_element_model_state(
                        new_state,
                        index,
                        key,
                    )
                else:
                    if old_child_state.is_component_state:
                        self._unmount_model_states([old_child_state])
                        new_child_state = _make_element_model_state(
                            new_state,
                            index,
                            key,
                        )
                        old_child_state = None
                    else:
                        new_child_state = _update_element_model_state(
                            old_child_state,
                            new_state,
                            index,
                        )
                self._render_model(exit_stack, old_child_state, new_child_state, child)
                new_state.append_child(new_child_state.model.current)
                new_state.children_by_key[key] = new_child_state
            elif child_type is _COMPONENT_TYPE:
                child = cast(ComponentType, child)
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is None:
                    new_child_state = _make_component_model_state(
                        new_state,
                        index,
                        key,
                        child,
                        self._rendering_queue.put,
                    )
                elif old_child_state.is_component_state and (
                    old_child_state.life_cycle_state.component.type != child.type
                ):
                    self._unmount_model_states([old_child_state])
                    old_child_state = None
                    new_child_state = _make_component_model_state(
                        new_state,
                        index,
                        key,
                        child,
                        self._rendering_queue.put,
                    )
                else:
                    new_child_state = _update_component_model_state(
                        old_child_state,
                        new_state,
                        index,
                        child,
                        self._rendering_queue.put,
                    )
                self._render_component(
                    exit_stack, old_child_state, new_child_state, child
                )
            else:
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is not None:
                    self._unmount_model_states([old_child_state])
                new_state.append_child(child)

    def _render_model_children_without_old_state(
        self,
        exit_stack: ExitStack,
        new_state: _ModelState,
        raw_children: List[Any],
    ) -> None:
        child_type_key_tuples = list(_process_child_type_and_key(raw_children))

        new_keys = {item[2] for item in child_type_key_tuples}
        if len(new_keys) != len(raw_children):
            key_counter = Counter(item[2] for item in child_type_key_tuples)
            duplicate_keys = [key for key, count in key_counter.items() if count > 1]
            raise ValueError(
                f"Duplicate keys {duplicate_keys} at {new_state.patch_path or '/'!r}"
            )

        new_state.model.current["children"] = []
        for index, (child, child_type, key) in enumerate(child_type_key_tuples):
            if child_type is _DICT_TYPE:
                child_state = _make_element_model_state(new_state, index, key)
                self._render_model(exit_stack, None, child_state, child)
                new_state.append_child(child_state.model.current)
                new_state.children_by_key[key] = child_state
            elif child_type is _COMPONENT_TYPE:
                child_state = _make_component_model_state(
                    new_state, index, key, child, self._rendering_queue.put
                )
                self._render_component(exit_stack, None, child_state, child)
            else:
                new_state.append_child(child)

    def _unmount_model_states(self, old_states: List[_ModelState]) -> None:
        to_unmount = old_states[::-1]  # unmount in reversed order of rendering
        while to_unmount:
            model_state = to_unmount.pop()

            for target in model_state.targets_by_event.values():
                del self._event_handlers[target]

            if model_state.is_component_state:
                life_cycle_state = model_state.life_cycle_state
                del self._model_states_by_life_cycle_state_id[life_cycle_state.id]
                life_cycle_state.hook.affect_component_will_unmount()

            to_unmount.extend(model_state.children_by_key.values())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.root})"


def _check_should_render(old: ComponentType, new: ComponentType) -> bool:
    try:
        return old.should_render(new)
    except Exception:
        logger.exception(f"{old} component failed to check if {new} should be rendered")
        return False


def _new_root_model_state(
    component: ComponentType, schedule_render: Callable[[_LifeCycleStateId], None]
) -> _ModelState:
    return _ModelState(
        parent=None,
        index=-1,
        key=None,
        model=Ref(),
        patch_path="",
        children_by_key={},
        targets_by_event={},
        life_cycle_state=_make_life_cycle_state(component, schedule_render),
    )


def _make_component_model_state(
    parent: _ModelState,
    index: int,
    key: Any,
    component: ComponentType,
    schedule_render: Callable[[_LifeCycleStateId], None],
) -> _ModelState:
    return _ModelState(
        parent=parent,
        index=index,
        key=key,
        model=Ref(),
        patch_path=f"{parent.patch_path}/children/{index}",
        children_by_key={},
        targets_by_event={},
        life_cycle_state=_make_life_cycle_state(component, schedule_render),
    )


def _copy_component_model_state(old_model_state: _ModelState) -> _ModelState:
    # use try/except here because not having a parent is rare (only the root state)
    try:
        parent: Optional[_ModelState] = old_model_state.parent
    except AttributeError:
        parent = None

    return _ModelState(
        parent=parent,
        index=old_model_state.index,
        key=old_model_state.key,
        model=Ref(),  # does not copy the model
        patch_path=old_model_state.patch_path,
        children_by_key={},
        targets_by_event={},
        life_cycle_state=old_model_state.life_cycle_state,
    )


def _update_component_model_state(
    old_model_state: _ModelState,
    new_parent: _ModelState,
    new_index: int,
    new_component: ComponentType,
    schedule_render: Callable[[_LifeCycleStateId], None],
) -> _ModelState:
    return _ModelState(
        parent=new_parent,
        index=new_index,
        key=old_model_state.key,
        model=Ref(),  # does not copy the model
        patch_path=old_model_state.patch_path,
        children_by_key={},
        targets_by_event={},
        life_cycle_state=(
            _update_life_cycle_state(old_model_state.life_cycle_state, new_component)
            if old_model_state.is_component_state
            else _make_life_cycle_state(new_component, schedule_render)
        ),
    )


def _make_element_model_state(
    parent: _ModelState,
    index: int,
    key: Any,
) -> _ModelState:
    return _ModelState(
        parent=parent,
        index=index,
        key=key,
        model=Ref(),
        patch_path=f"{parent.patch_path}/children/{index}",
        children_by_key={},
        targets_by_event={},
    )


def _update_element_model_state(
    old_model_state: _ModelState,
    new_parent: _ModelState,
    new_index: int,
) -> _ModelState:
    return _ModelState(
        parent=new_parent,
        index=new_index,
        key=old_model_state.key,
        model=Ref(),  # does not copy the model
        patch_path=old_model_state.patch_path,
        children_by_key={},
        targets_by_event={},
    )


class _ModelState:
    """State that is bound to a particular element within the layout"""

    __slots__ = (
        "__weakref__",
        "_parent_ref",
        "children_by_key",
        "index",
        "key",
        "life_cycle_state",
        "model",
        "patch_path",
        "targets_by_event",
    )

    def __init__(
        self,
        parent: Optional[_ModelState],
        index: int,
        key: Any,
        model: Ref[VdomJson],
        patch_path: str,
        children_by_key: Dict[str, _ModelState],
        targets_by_event: Dict[str, str],
        life_cycle_state: Optional[_LifeCycleState] = None,
    ):
        self.index = index
        """The index of the element amongst its siblings"""

        self.key = key
        """A key that uniquely identifies the element amongst its siblings"""

        self.model = model
        """The actual model of the element"""

        self.patch_path = patch_path
        """A "/" delimitted path to the element within the greater layout"""

        self.children_by_key = children_by_key
        """Child model states indexed by their unique keys"""

        self.targets_by_event = targets_by_event
        """The element's event handler target strings indexed by their event name"""

        # === Conditionally Available Attributes ===
        # It's easier to conditionally assign than to force a null check on every usage

        if parent is not None:
            self._parent_ref = weakref(parent)
            """The parent model state"""

        if life_cycle_state is not None:
            self.life_cycle_state = life_cycle_state
            """The state for the element's component (if it has one)"""

    @property
    def is_component_state(self) -> bool:
        return hasattr(self, "life_cycle_state")

    @property
    def parent(self) -> _ModelState:
        parent = self._parent_ref()
        assert parent is not None, "detached model state"
        return parent

    def append_child(self, child: Any) -> None:
        self.model.current["children"].append(child)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ModelState({ {s: getattr(self, s, None) for s in self.__slots__} })"


def _make_life_cycle_state(
    component: ComponentType,
    schedule_render: Callable[[_LifeCycleStateId], None],
) -> _LifeCycleState:
    life_cycle_state_id = _LifeCycleStateId(uuid4().hex)
    return _LifeCycleState(
        life_cycle_state_id,
        LifeCycleHook(lambda: schedule_render(life_cycle_state_id)),
        component,
    )


def _update_life_cycle_state(
    old_life_cycle_state: _LifeCycleState,
    new_component: ComponentType,
) -> _LifeCycleState:
    return _LifeCycleState(
        old_life_cycle_state.id,
        # the hook is preserved across renders because it holds the state
        old_life_cycle_state.hook,
        new_component,
    )


_LifeCycleStateId = NewType("_LifeCycleStateId", str)


class _LifeCycleState(NamedTuple):
    """Component state for :class:`_ModelState`"""

    id: _LifeCycleStateId
    """A unique identifier used in the :class:`~idom.core.hooks.LifeCycleHook` callback"""

    hook: LifeCycleHook
    """The life cycle hook"""

    component: ComponentType
    """The current component instance"""


_Type = TypeVar("_Type")


class _ThreadSafeQueue(Generic[_Type]):

    __slots__ = "_loop", "_queue", "_pending"

    def __init__(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._queue: asyncio.Queue[_Type] = asyncio.Queue()
        self._pending: Set[_Type] = set()

    def put(self, value: _Type) -> None:
        if value not in self._pending:
            self._pending.add(value)
            self._loop.call_soon_threadsafe(self._queue.put_nowait, value)
        return None

    def remove_if_pending(self, value: _Type) -> None:
        if value in self._pending:
            self._pending.remove(value)

    async def get(self) -> _Type:
        while True:
            value = await self._queue.get()
            if value in self._pending:
                break
        self._pending.remove(value)
        return value


def _process_child_type_and_key(
    children: List[Any],
) -> Iterator[Tuple[Any, _ElementType, Any]]:
    for index, child in enumerate(children):
        if isinstance(child, dict):
            child_type = _DICT_TYPE
            key = child.get("key")
        elif isinstance(child, ComponentType):
            child_type = _COMPONENT_TYPE
            key = getattr(child, "key", None)
        else:
            child = f"{child}"
            child_type = _STRING_TYPE
            key = None

        if key is None:
            key = index

        yield (child, child_type, key)


# used in _process_child_type_and_key
_ElementType = NewType("_ElementType", int)
_DICT_TYPE = _ElementType(1)
_COMPONENT_TYPE = _ElementType(2)
_STRING_TYPE = _ElementType(3)
