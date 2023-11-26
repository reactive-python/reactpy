from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, Callable, TypeVar

from anyio import Semaphore

from reactpy.core._thread_local import ThreadLocal
from reactpy.core.types import ComponentType, Context, ContextProviderType

T = TypeVar("T")

StopEffect = Callable[[], Coroutine[None, None, None]]
StartEffect = Callable[[], Coroutine[None, None, StopEffect]]

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
    """Defines the life cycle of a layout component.

    Components can request access to their own life cycle events and state through hooks
    while :class:`~reactpy.core.proto.LayoutType` objects drive drive the life cycle
    forward by triggering events and rendering view changes.

    Example:

        If removed from the complexities of a layout, a very simplified full life cycle
        for a single component with no child components would look a bit like this:

        .. testcode::

            from reactpy.core._life_cycle_hooks import LifeCycleHook
            from reactpy.core.hooks import current_hook, COMPONENT_DID_RENDER_EFFECT

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
                current_hook().add_effect(COMPONENT_DID_RENDER_EFFECT, lambda: ...)
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
        "_effect_starts",
        "_effect_stops",
        "_render_access",
        "_rendered_atleast_once",
        "_schedule_render_callback",
        "_schedule_render_later",
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
        self._schedule_render_later = False
        self._rendered_atleast_once = False
        self._current_state_index = 0
        self._state: tuple[Any, ...] = ()
        self._effect_starts: list[StartEffect] = []
        self._effect_stops: list[StopEffect] = []
        self._render_access = Semaphore(1)  # ensure only one render at a time

    def schedule_render(self) -> None:
        if self._is_rendering():
            self._schedule_render_later = True
        else:
            self._schedule_render()

    def use_state(self, function: Callable[[], T]) -> T:
        if not self._rendered_atleast_once:
            # since we're not initialized yet we're just appending state
            result = function()
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result

    def add_effect(self, start_effect: StartEffect) -> None:
        """Add an effect to this hook"""
        self._effect_starts.append(start_effect)

    def set_context_provider(self, provider: ContextProviderType[Any]) -> None:
        self._context_providers[provider.type] = provider

    def get_context_provider(
        self, context: Context[T]
    ) -> ContextProviderType[T] | None:
        return self._context_providers.get(context)

    async def affect_component_will_render(self, component: ComponentType) -> None:
        """The component is about to render"""
        await self._render_access.acquire()
        self.component = component
        self.set_current()

    async def affect_component_did_render(self) -> None:
        """The component completed a render"""
        self.unset_current()
        del self.component
        self._rendered_atleast_once = True
        self._current_state_index = 0
        self._render_access.release()

    async def affect_layout_did_render(self) -> None:
        """The layout completed a render"""
        self._effect_stops.extend(
            await asyncio.gather(*[start() for start in self._effect_starts])
        )
        self._effect_starts.clear()

        if self._schedule_render_later:
            self._schedule_render()
        self._schedule_render_later = False

    async def affect_component_will_unmount(self) -> None:
        """The component is about to be removed from the layout"""
        try:
            await asyncio.gather(*[stop() for stop in self._effect_stops])
        except Exception:  # nocov
            logger.exception("Error during effect cancellation")
        finally:
            self._effect_stops.clear()

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

    def _is_rendering(self) -> bool:
        return self._render_access.value != 0

    def _schedule_render(self) -> None:
        try:
            self._schedule_render_callback()
        except Exception:
            logger.exception(
                f"Failed to schedule render via {self._schedule_render_callback}"
            )
