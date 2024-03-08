from __future__ import annotations

import abc
import asyncio
import copy
from asyncio import (
    FIRST_COMPLETED,
    CancelledError,
    PriorityQueue,
    Queue,
    Task,
    create_task,
    get_running_loop,
    wait,
)
from collections import Counter
from collections.abc import Sequence
from contextlib import AsyncExitStack
from logging import getLogger
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    NamedTuple,
    NewType,
    TypeVar,
    cast,
)
from uuid import uuid4
from weakref import ref as weakref

from anyio import Semaphore
from typing_extensions import TypeAlias

from reactpy.config import (
    REACTPY_ASYNC_RENDERING,
    REACTPY_CHECK_VDOM_SPEC,
    REACTPY_DEBUG_MODE,
)
from reactpy.core._life_cycle_hook import (
    LifeCycleHook,
    clear_hook_state,
    create_hook_state,
    get_hook_state,
)
from reactpy.core.component import Component
from reactpy.core.hooks import _ContextProvider
from reactpy.core.state_recovery import (
    StateRecoveryFailureError,
    StateRecoverySerializer,
)
from reactpy.core.types import (
    ComponentType,
    EventHandlerDict,
    Key,
    LayoutEventMessage,
    LayoutUpdateMessage,
    StateUpdateMessage,
    VdomChild,
    VdomDict,
    VdomJson,
)
from reactpy.core.vdom import validate_vdom_json
from reactpy.utils import Ref

logger = getLogger(__name__)


class Layout:
    """Responsible for "rendering" components. That is, turning them into VDOM."""

    __slots__: tuple[str, ...] = (
        "root",
        "_event_handlers",
        "_rendering_queue",
        "_render_tasks",
        "_render_tasks_ready",
        "_root_life_cycle_state_id",
        "_model_states_by_life_cycle_state_id",
        "reconnecting",
        "client_state",
        "_state_recovery_serializer",
        "_state_var_lock",
        "_hook_state_token",
        "_previous_states",
    )

    if not hasattr(abc.ABC, "__weakref__"):  # nocov
        __slots__ += ("__weakref__",)

    def __init__(
        self,
        root: ComponentType,
    ) -> None:
        super().__init__()
        # slow
        # if not isinstance(root, ComponentType):
        #     msg = f"Expected a ComponentType, not {type(root)!r}."
        #     raise TypeError(msg)
        self.root = root
        self.reconnecting = Ref(False)
        self._state_recovery_serializer = None
        self.client_state = {}
        self._previous_states = {}

    def set_recovery_serializer(self, serializer: StateRecoverySerializer) -> None:
        self._state_recovery_serializer = serializer

    async def __aenter__(self) -> Layout:
        return await self.start()

    async def start(self) -> Layout:
        self._hook_state_token = create_hook_state()

        # create attributes here to avoid access before entering context manager
        self._event_handlers: EventHandlerDict = {}
        self._render_tasks: set[Task[LayoutUpdateMessage]] = set()
        self._render_tasks_ready: Semaphore = Semaphore(0)

        self._rendering_queue: _ThreadSafeQueue[_LifeCycleStateId] = _ThreadSafeQueue()
        root_model_state = _new_root_model_state(
            self.root,
            self._schedule_render_task,
            self.reconnecting,
            self.client_state,
            self._previous_states,
        )

        self._root_life_cycle_state_id = root_id = root_model_state.life_cycle_state.id
        self._model_states_by_life_cycle_state_id = {root_id: root_model_state}

        return self

    async def __aexit__(self, *exc: Any) -> None:
        return await self.finish()

    async def finish(self) -> None:
        root_csid = self._root_life_cycle_state_id
        root_model_state = self._model_states_by_life_cycle_state_id[root_csid]

        for t in self._render_tasks:
            t.cancel()
            try:
                await t
            except CancelledError:
                pass

        await self._unmount_model_states([root_model_state])

        # delete attributes here to avoid access after exiting context manager
        del self._event_handlers
        del self._rendering_queue
        del self._root_life_cycle_state_id
        del self._model_states_by_life_cycle_state_id

        clear_hook_state(self._hook_state_token)

    def start_rendering(self) -> None:
        self._schedule_render_task(self._root_life_cycle_state_id)

    def start_rendering_for_reconnect(self) -> None:
        self._rendering_queue.put(self._root_life_cycle_state_id)

    async def deliver(self, event: LayoutEventMessage) -> None:
        """Dispatch an event to the targeted handler"""
        # It is possible for an element in the frontend to produce an event
        # associated with a backend model that has been deleted. We only handle
        # events if the element and the handler exist in the backend. Otherwise
        # we just ignore the event.
        handler = self._event_handlers.get(event["target"])

        if handler is not None:
            try:
                await handler.function(event["data"])
            except Exception:
                logger.exception(f"Failed to execute event handler {handler}")
        else:
            logger.warning(
                f"Ignored event - handler {event['target']!r} "
                "does not exist or its component unmounted"
            )

    async def render(self) -> LayoutUpdateMessage:
        if REACTPY_ASYNC_RENDERING.current:
            return await self._concurrent_render()
        else:  # nocov
            return await self._serial_render()

    async def render_until_queue_empty(self) -> None:
        model_state_id = await self._rendering_queue.get()
        while True:
            try:
                model_state = self._model_states_by_life_cycle_state_id[model_state_id]
            except KeyError:
                logger.debug(
                    "Did not render component with model state ID "
                    f"{model_state_id!r} - component already unmounted"
                )
            else:
                await self._create_layout_update(model_state, get_hook_state())
            # this might seem counterintuitive. What's happening is that events can get kicked off
            # and currently there's no (obvious) visibility on if we're waiting for them to finish
            # so this will wait up to 0.15 * 5 = 750 ms to see if any renders come in before
            # declaring it done. In the future, it would be better to just track the pending events
            for _ in range(5):
                try:
                    model_state_id = await self._rendering_queue.get_nowait()
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.15)  # make sure
                else:
                    break
            else:
                return

    async def _serial_render(self) -> LayoutUpdateMessage:  # nocov
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
                return await self._create_layout_update(model_state, get_hook_state())

    async def _concurrent_render(self) -> LayoutUpdateMessage:
        """Await the next available render. This will block until a component is updated"""
        await self._render_tasks_ready.acquire()
        done, _ = await wait(self._render_tasks, return_when=FIRST_COMPLETED)
        update_task: Task[LayoutUpdateMessage] = done.pop()
        self._render_tasks.remove(update_task)
        return update_task.result()

    async def _create_layout_update(
        self, old_state: _ModelState, incoming_hook_state: list
    ) -> LayoutUpdateMessage:
        token = create_hook_state(copy.copy(incoming_hook_state))
        new_state = _copy_component_model_state(old_state)
        component = new_state.life_cycle_state.component

        async with AsyncExitStack() as exit_stack:
            await self._render_component(exit_stack, old_state, new_state, component)

        if REACTPY_CHECK_VDOM_SPEC.current:
            validate_vdom_json(new_state.model.current)

        updated_states = new_state.life_cycle_state.hook._updated_states
        state_vars = (
            (await self._state_recovery_serializer.serialize_state_vars(updated_states))
            if self._state_recovery_serializer
            else {}
        )
        self._previous_states.update(updated_states)
        updated_states.clear()
        clear_hook_state(token)
        return LayoutUpdateMessage(
            type="layout-update",
            path=new_state.patch_path,
            model=new_state.model.current,
            state_vars=state_vars,
        )

    async def _render_component(
        self,
        exit_stack: AsyncExitStack,
        old_state: _ModelState | None,
        new_state: _ModelState,
        component: ComponentType,
    ) -> None:
        life_cycle_state = new_state.life_cycle_state
        life_cycle_hook = life_cycle_state.hook

        self._model_states_by_life_cycle_state_id[life_cycle_state.id] = new_state

        await life_cycle_hook.affect_component_will_render(component)
        exit_stack.push_async_callback(life_cycle_hook.affect_layout_did_render)
        try:
            patch_path_for_state = new_state.patch_path  # type: ignore  # noqa
            raw_model = component.render()
            # wrap the model in a fragment (i.e. tagName="") to ensure components have
            # a separate node in the model state tree. This could be removed if this
            # components are given a node in the tree some other way
            wrapper_model: VdomDict = {"tagName": "", "children": [raw_model]}
            await self._render_model(exit_stack, old_state, new_state, wrapper_model)
        except StateRecoveryFailureError:
            raise
        except Exception as error:
            logger.exception(f"Failed to render {component}")
            new_state.model.current = {
                "tagName": "",
                "error": (
                    f"{type(error).__name__}: {error}"
                    if REACTPY_DEBUG_MODE.current
                    else ""
                ),
            }
        finally:
            await life_cycle_hook.affect_component_did_render()

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
                **old_parent_model,
                "children": [
                    *old_parent_children[:index],
                    new_state.model.current,
                    *old_parent_children[index + 1 :],
                ],
            }

    async def _render_model(
        self,
        exit_stack: AsyncExitStack,
        old_state: _ModelState | None,
        new_state: _ModelState,
        raw_model: Any,
    ) -> None:
        try:
            new_state.model.current = {"tagName": raw_model["tagName"]}
        except Exception as e:  # nocov
            msg = f"Expected a VDOM element dict, not {raw_model}"
            raise ValueError(msg) from e
        if "key" in raw_model:
            new_state.key = new_state.model.current["key"] = raw_model["key"]
        if "importSource" in raw_model:
            new_state.model.current["importSource"] = raw_model["importSource"]
        self._render_model_attributes(old_state, new_state, raw_model)
        await self._render_model_children(
            exit_stack, old_state, new_state, raw_model.get("children", [])
        )

    def _render_model_attributes(
        self,
        old_state: _ModelState | None,
        new_state: _ModelState,
        raw_model: dict[str, Any],
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
                target = (
                    new_state.patch_path + event
                    if handler.target is None
                    else handler.target
                )
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
            target = (
                new_state.patch_path + event
                if handler.target is None
                else handler.target
            )
            new_state.targets_by_event[event] = target
            self._event_handlers[target] = handler
            model_event_handlers[event] = {
                "target": target,
                "preventDefault": handler.prevent_default,
                "stopPropagation": handler.stop_propagation,
            }

        return None

    async def _render_model_children(
        self,
        exit_stack: AsyncExitStack,
        old_state: _ModelState | None,
        new_state: _ModelState,
        raw_children: Any,
    ) -> None:
        if not isinstance(raw_children, (list, tuple)):
            raw_children = [raw_children]

        if old_state is None:
            if raw_children:
                await self._render_model_children_without_old_state(
                    exit_stack, new_state, raw_children
                )
            return None
        elif not raw_children:
            await self._unmount_model_states(list(old_state.children_by_key.values()))
            return None

        children_info = _get_children_info(raw_children)

        new_keys = {k for _, _, k in children_info}
        if len(new_keys) != len(children_info):
            key_counter = Counter(item[2] for item in children_info)
            duplicate_keys = [key for key, count in key_counter.items() if count > 1]
            msg = f"Duplicate keys {duplicate_keys} at {new_state.patch_path or '/'!r}"
            raise ValueError(msg)

        old_keys = set(old_state.children_by_key).difference(new_keys)
        if old_keys:
            await self._unmount_model_states(
                [old_state.children_by_key[key] for key in old_keys]
            )

        new_state.model.current["children"] = []
        for index, (child, child_type, key) in enumerate(children_info):
            old_child_state = old_state.children_by_key.get(key)
            if child_type is _DICT_TYPE:
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is None:
                    new_child_state = _make_element_model_state(
                        new_state,
                        index,
                        key,
                    )
                elif old_child_state.is_component_state:
                    await self._unmount_model_states([old_child_state])
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
                await self._render_model(
                    exit_stack, old_child_state, new_child_state, child
                )
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
                        self._schedule_render_task,
                        self.reconnecting,
                        self.client_state,
                    )
                elif old_child_state.is_component_state and (
                    old_child_state.life_cycle_state.component.type != child.type
                ):
                    await self._unmount_model_states([old_child_state])
                    old_child_state = None
                    new_child_state = _make_component_model_state(
                        new_state,
                        index,
                        key,
                        child,
                        self._schedule_render_task,
                        self.reconnecting,
                        self.client_state,
                    )
                else:
                    new_child_state = _update_component_model_state(
                        old_child_state,
                        new_state,
                        index,
                        child,
                        self._schedule_render_task,
                        self.reconnecting,
                        self.client_state,
                    )
                await self._render_component(
                    exit_stack, old_child_state, new_child_state, child
                )
            else:
                old_child_state = old_state.children_by_key.get(key)
                if old_child_state is not None:
                    await self._unmount_model_states([old_child_state])
                new_state.append_child(child)

    async def _render_model_children_without_old_state(
        self,
        exit_stack: AsyncExitStack,
        new_state: _ModelState,
        raw_children: list[Any],
    ) -> None:
        children_info = _get_children_info(raw_children)

        new_keys = {k for _, _, k in children_info}
        if len(new_keys) != len(children_info):
            key_counter = Counter(k for _, _, k in children_info)
            duplicate_keys = [key for key, count in key_counter.items() if count > 1]
            msg = f"Duplicate keys {duplicate_keys} at {new_state.patch_path or '/'!r}"
            raise ValueError(msg)

        new_state.model.current["children"] = []
        for index, (child, child_type, key) in enumerate(children_info):
            if child_type is _DICT_TYPE:
                child_state = _make_element_model_state(new_state, index, key)
                await self._render_model(exit_stack, None, child_state, child)
                new_state.append_child(child_state.model.current)
                new_state.children_by_key[key] = child_state
            elif child_type is _COMPONENT_TYPE:
                child_state = _make_component_model_state(
                    new_state,
                    index,
                    key,
                    child,
                    self._schedule_render_task,
                    self.reconnecting,
                    self.client_state,
                )
                await self._render_component(exit_stack, None, child_state, child)
            else:
                new_state.append_child(child)

    async def _unmount_model_states(self, old_states: list[_ModelState]) -> None:
        to_unmount = old_states[::-1]  # unmount in reversed order of rendering
        while to_unmount:
            model_state = to_unmount.pop()

            for target in model_state.targets_by_event.values():
                del self._event_handlers[target]

            if model_state.is_component_state:
                life_cycle_state = model_state.life_cycle_state
                try:
                    del self._model_states_by_life_cycle_state_id[life_cycle_state.id]
                    await life_cycle_state.hook.affect_component_will_unmount()
                except KeyError:
                    pass  # sideeffect of reusing model states

            to_unmount.extend(model_state.children_by_key.values())

    def _schedule_render_task(
        self, lcs_id: _LifeCycleStateId, priority: int = 0
    ) -> None:
        if not REACTPY_ASYNC_RENDERING.current:
            self._rendering_queue.put(lcs_id, priority)
            return None
        try:
            model_state = self._model_states_by_life_cycle_state_id[lcs_id]
        except KeyError:
            logger.debug(
                "Did not render component with model state ID "
                f"{lcs_id!r} - component already unmounted"
            )
        else:
            self._render_tasks.add(create_task(self._create_layout_update(model_state)))
            self._render_tasks_ready.release()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.root})"


def _new_root_model_state(
    component: ComponentType,
    schedule_render: Callable[[_LifeCycleStateId], None],
    reconnecting: bool,
    client_state: dict[str, Any],
    previous_states: dict[str, Any],
) -> _ModelState:
    return _ModelState(
        parent=None,
        index=-1,
        key=None,
        model=Ref(),
        patch_path="",
        children_by_key={},
        targets_by_event={},
        life_cycle_state=_make_life_cycle_state(
            component, schedule_render, reconnecting, client_state, {}, previous_states
        ),
    )


def _make_component_model_state(
    parent: _ModelState,
    index: int,
    key: Any,
    component: ComponentType,
    schedule_render: Callable[[_LifeCycleStateId, int], None],
    reconnecting: bool,
    client_state: dict[str, Any],
) -> _ModelState:
    hook = (parent.life_cycle_state or parent.parent_life_cycle_state).hook
    return _ModelState(
        parent=parent,
        index=index,
        key=key,
        model=Ref(),
        patch_path=f"{parent.patch_path}/children/{index}",
        children_by_key={},
        targets_by_event={},
        life_cycle_state=_make_life_cycle_state(
            component,
            schedule_render,
            reconnecting,
            client_state,
            hook._updated_states,
            hook._previous_states,
        ),
    )


def _copy_component_model_state(old_model_state: _ModelState) -> _ModelState:
    # use try/except here because not having a parent is rare (only the root state)
    try:
        parent: _ModelState | None = old_model_state.parent
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
    schedule_render: Callable[[_LifeCycleStateId, int], None],
    reconnecting: bool,
    client_state: dict[str, Any],
) -> _ModelState:
    hook = (new_parent.life_cycle_state or new_parent.parent_life_cycle_state).hook
    return _ModelState(
        parent=new_parent,
        index=new_index,
        key=old_model_state.key,
        model=Ref(),  # does not copy the model
        patch_path=f"{new_parent.patch_path}/children/{new_index}",
        children_by_key={},
        targets_by_event={},
        life_cycle_state=(
            _update_life_cycle_state(old_model_state.life_cycle_state, new_component)
            if old_model_state.is_component_state
            else _make_life_cycle_state(
                new_component,
                schedule_render,
                reconnecting,
                client_state,
                hook._updated_states,
                hook._previous_states,
            )
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
        parent_life_cycle_state=(
            parent.life_cycle_state or parent.parent_life_cycle_state
        ),
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
        parent_life_cycle_state=(
            new_parent.life_cycle_state or new_parent.parent_life_cycle_state
        ),
    )


class _ModelState:
    """State that is bound to a particular element within the layout"""

    __slots__ = (
        "__weakref__",
        "_parent_ref",
        "_render_semaphore",
        "children_by_key",
        "index",
        "key",
        "life_cycle_state",
        "parent_life_cycle_state",
        "model",
        "patch_path",
        "targets_by_event",
    )

    def __init__(
        self,
        parent: _ModelState | None,
        index: int,
        key: Any,
        model: Ref[VdomJson],
        patch_path: str,
        children_by_key: dict[Key, _ModelState],
        targets_by_event: dict[str, str],
        life_cycle_state: _LifeCycleState | None = None,
        parent_life_cycle_state: _LifeCycleState | None = None,
    ):
        self.index = index
        """The index of the element amongst its siblings"""

        self.key = key
        """A key that uniquely identifies the element amongst its siblings"""

        self.model = model
        """The actual model of the element"""

        self.patch_path = patch_path
        """A "/" delimited path to the element within the greater layout"""

        self.children_by_key = children_by_key
        """Child model states indexed by their unique keys"""

        self.targets_by_event = targets_by_event
        """The element's event handler target strings indexed by their event name"""

        # === Conditionally Available Attributes ===
        # It's easier to conditionally assign than to force a null check on every usage

        if parent is not None:
            self._parent_ref = weakref(parent)
            """The parent model state"""

        self.life_cycle_state = life_cycle_state
        """The state for the element's component (if it has one)"""

        self.parent_life_cycle_state = parent_life_cycle_state

    @property
    def is_component_state(self) -> bool:
        return self.life_cycle_state is not None

    @property
    def parent(self) -> _ModelState:
        parent = self._parent_ref()
        if parent is None:
            raise RuntimeError("detached model state")  # nocov
        return parent

    def append_child(self, child: Any) -> None:
        self.model.current["children"].append(child)

    def __repr__(self) -> str:  # nocov
        return f"ModelState({ {s: getattr(self, s, None) for s in self.__slots__} })"


def _make_life_cycle_state(
    component: ComponentType,
    schedule_render: Callable[[_LifeCycleStateId, int], None],
    reconnecting: bool,
    client_state: dict[str, Any],
    updated_states: dict[str, Any],
    previous_states: dict[str, Any],
) -> _LifeCycleState:
    life_cycle_state_id = _LifeCycleStateId(uuid4().hex)
    return _LifeCycleState(
        life_cycle_state_id,
        LifeCycleHook(
            lambda: schedule_render(life_cycle_state_id, component.priority),
            reconnecting=reconnecting,
            client_state=client_state,
            updated_states=updated_states,
            previous_states=previous_states,
        ),
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
    """A unique identifier used in the :class:`~reactpy.core.hooks.LifeCycleHook` callback"""

    hook: LifeCycleHook
    """The life cycle hook"""

    component: ComponentType
    """The current component instance"""


_Type = TypeVar("_Type")


class _ThreadSafeQueue(Generic[_Type]):
    def __init__(self) -> None:
        self._loop = get_running_loop()
        self._queue: PriorityQueue[_Type] = PriorityQueue()
        self._pending: set[_Type] = set()

    def put(self, value: _Type, priority: int = 0) -> None:
        if value not in self._pending:
            self._pending.add(value)
            self._loop.call_soon_threadsafe(self._queue.put_nowait, (priority, value))

    async def get(self) -> _Type:
        priority, value = await self._queue.get()
        self._pending.remove(value)
        return value

    async def get_nowait(self) -> _Type:
        priority, value = self._queue.get_nowait()
        self._pending.remove(value)
        return value


def _get_children_info(children: list[VdomChild]) -> Sequence[_ChildInfo]:
    infos: list[_ChildInfo] = []
    for index, child in enumerate(children):
        if child is None:
            continue
        elif isinstance(child, dict):
            child_type = _DICT_TYPE
            key = child.get("key")
        elif isinstance(child, (Component, _ContextProvider)):
            child_type = _COMPONENT_TYPE
            key = child.key
        else:
            child = f"{child}"
            child_type = _STRING_TYPE
            key = None

        if key is None:
            key = index

        infos.append((child, child_type, key))

    return infos


_ChildInfo: TypeAlias = tuple[Any, "_ElementType", Key]

# used in _process_child_type_and_key
_ElementType = NewType("_ElementType", int)
_DICT_TYPE = _ElementType(1)
_COMPONENT_TYPE = _ElementType(2)
_STRING_TYPE = _ElementType(3)
