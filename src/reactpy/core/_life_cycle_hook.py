from __future__ import annotations

import logging
from asyncio import Event, Task, create_task, gather
from typing import Any, Callable, Protocol, TypeVar

from anyio import Semaphore

from reactpy.core._thread_local import ThreadLocal
from reactpy.core.types import ComponentType, Context, ContextProviderType

T = TypeVar("T")


class EffectFunc(Protocol):
    async def __call__(self, stop: Event) -> None: ...


logger = logging.getLogger(__name__)

_HOOK_STATE: ThreadLocal[list[LifeCycleHook]] = ThreadLocal(list)


def current_hook() -> LifeCycleHook:
    """Get the current :class:`LifeCycleHook`"""
    hook_stack = _HOOK_STATE.get()
    if not hook_stack:
        msg = "No life cycle hook is active. Are you rendering in a layout?"
        raise RuntimeError(msg)
    return hook_stack[-1]


class LifeCycleHook:
    """An object which manages the "life cycle" of a layout component.

    The "life cycle" of a component is the set of events which occur from the time
    a component is first rendered until it is removed from the layout. The life cycle
    is ultimately driven by the layout itself, but components can "hook" into those
    events to perform actions. Components gain access to their own life cycle hook
    by calling :func:`current_hook`. They can then perform actions such as:

    1. Adding state via :meth:`use_state`
    2. Adding effects via :meth:`add_effect`
    3. Setting or getting context providers via
       :meth:`LifeCycleHook.set_context_provider` and
       :meth:`get_context_provider` respectively.

    Components can request access to their own life cycle events and state through hooks
    while :class:`~reactpy.core.proto.LayoutType` objects drive drive the life cycle
    forward by triggering events and rendering view changes.

    Example:

        If removed from the complexities of a layout, a very simplified full life cycle
        for a single component with no child components would look a bit like this:

        .. testcode::

            from reactpy.core._life_cycle_hook import LifeCycleHook
            from reactpy.core.hooks import current_hook

            # this function will come from a layout implementation
            schedule_render = lambda: ...

            # --- start life cycle ---

            hook = LifeCycleHook(schedule_render)

            # --- start render cycle ---

            component = ...
            await hook.affect_component_will_render(component)
            try:
                # render the component
                ...

                # the component may access the current hook
                assert current_hook() is hook

                # and save state or add effects
                current_hook().use_state(lambda: ...)

                async def my_effect(stop_event):
                    ...

                current_hook().add_effect(my_effect)
            finally:
                await hook.affect_component_did_render()

            # This should only be called after the full set of changes associated with a
            # given render have been completed.
            await hook.affect_layout_did_render()

            # Typically an event occurs and a new render is scheduled, thus beginning
            # the render cycle anew.
            hook.schedule_render()


            # --- end render cycle ---

            hook.affect_component_will_unmount()
            del hook

            # --- end render cycle ---
    """

    __slots__ = (
        "__weakref__",
        "_context_providers",
        "_current_state_index",
        "_effect_funcs",
        "_effect_stops",
        "_effect_tasks",
        "_render_access",
        "_rendered_atleast_once",
        "_schedule_render_callback",
        "_scheduled_render",
        "_state",
        "component",
    )

    component: ComponentType

    def __init__(
        self,
        schedule_render: Callable[[], None],
    ) -> None:
        self._context_providers: dict[Context[Any], ContextProviderType[Any]] = {}
        self._schedule_render_callback = schedule_render
        self._scheduled_render = False
        self._rendered_atleast_once = False
        self._current_state_index = 0
        self._state: tuple[Any, ...] = ()
        self._effect_funcs: list[EffectFunc] = []
        self._effect_tasks: list[Task[None]] = []
        self._effect_stops: list[Event] = []
        self._render_access = Semaphore(1)  # ensure only one render at a time

    def schedule_render(self) -> None:
        if self._scheduled_render:
            return None
        try:
            self._schedule_render_callback()
        except Exception:
            msg = f"Failed to schedule render via {self._schedule_render_callback}"
            logger.exception(msg)
        else:
            self._scheduled_render = True

    def use_state(self, function: Callable[[], T]) -> T:
        """Add state to this hook

        If this hook has not yet rendered, the state is appended to the state tuple.
        Otherwise, the state is retrieved from the tuple. This allows state to be
        preserved across renders.
        """
        if not self._rendered_atleast_once:
            # since we're not initialized yet we're just appending state
            result = function()
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result

    def add_effect(self, effect_func: EffectFunc) -> None:
        """Add an effect to this hook

        A task to run the effect is created when the component is done rendering.
        When the component will be unmounted, the event passed to the effect is
        triggered and the task is awaited. The effect should eventually halt after
        the event is triggered.
        """
        self._effect_funcs.append(effect_func)

    def set_context_provider(self, provider: ContextProviderType[Any]) -> None:
        """Set a context provider for this hook

        The context provider will be used to provide state to any child components
        of this hook's component which request a context provider of the same type.
        """
        self._context_providers[provider.type] = provider

    def get_context_provider(
        self, context: Context[T]
    ) -> ContextProviderType[T] | None:
        """Get a context provider for this hook of the given type

        The context provider will have been set by a parent component. If no provider
        is found, ``None`` is returned.
        """
        return self._context_providers.get(context)

    async def affect_component_will_render(self, component: ComponentType) -> None:
        """The component is about to render"""
        await self._render_access.acquire()
        self._scheduled_render = False
        self.component = component
        self.set_current()

    async def affect_component_did_render(self) -> None:
        """The component completed a render"""
        self.unset_current()
        self._rendered_atleast_once = True
        self._current_state_index = 0
        self._render_access.release()
        del self.component

    async def affect_layout_did_render(self) -> None:
        """The layout completed a render"""
        stop = Event()
        self._effect_stops.append(stop)
        self._effect_tasks.extend(create_task(e(stop)) for e in self._effect_funcs)
        self._effect_funcs.clear()

    async def affect_component_will_unmount(self) -> None:
        """The component is about to be removed from the layout"""
        for stop in self._effect_stops:
            stop.set()
        self._effect_stops.clear()
        try:
            await gather(*self._effect_tasks)
        except Exception:
            logger.exception("Error in effect")
        finally:
            self._effect_tasks.clear()

    def set_current(self) -> None:
        """Set this hook as the active hook in this thread

        This method is called by a layout before entering the render method
        of this hook's associated component.
        """
        hook_stack = _HOOK_STATE.get()
        if hook_stack:
            parent = hook_stack[-1]
            self._context_providers.update(parent._context_providers)
        hook_stack.append(self)

    def unset_current(self) -> None:
        """Unset this hook as the active hook in this thread"""
        if _HOOK_STATE.get().pop() is not self:
            raise RuntimeError("Hook stack is in an invalid state")  # nocov
