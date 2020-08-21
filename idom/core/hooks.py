import asyncio
import inspect
from functools import lru_cache
from threading import get_ident as get_thread_id
from typing import (
    cast,
    Dict,
    Any,
    TypeVar,
    Callable,
    Tuple,
    Awaitable,
    Optional,
    Generic,
    Union,
    NamedTuple,
    List,
)

from .element import AbstractElement


__all__ = [
    "use_update",
    "use_state",
    "use_memo",
    "use_lru_cache",
]


def use_update() -> Callable[[], None]:
    return current_hook().use_update()


_StateType = TypeVar("_StateType")


class Shared(Generic[_StateType]):

    __slots__ = "_callbacks", "_value"

    def __init__(self, value: _StateType) -> None:
        self._callbacks: Dict[str, Callable[[_StateType], None]] = {}
        self._value = value

    def update(self, value: _StateType) -> None:
        self._value = value
        for cb in self._callbacks.values():
            cb(value)


def _new_is_not_old(old: _StateType, new: _StateType) -> bool:
    return new is not old


def use_state(
    value: Union[_StateType, Callable[[], _StateType], Shared[_StateType]],
    should_update: Callable[[_StateType, _StateType], bool] = _new_is_not_old,
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    if isinstance(value, Shared):
        return _use_shared(value, should_update)
    else:
        return _use_state(value, should_update)


def _use_shared(
    shared: Shared[_StateType], should_update: Callable[[_StateType, _StateType], bool],
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    hook = current_hook()
    update = hook.use_update()

    old = shared._value

    def add_callback(cleanup):
        shared._callbacks[hook.element_id] = (
            lambda new: update() if should_update(new, old) else None
        )
        cleanup(shared._callbacks.pop, hook.element_id, None)

    use_effect(add_callback)

    def set_state(new: _StateType) -> None:
        shared.update(new)

    return shared._value, set_state


def _use_state(
    value: Union[_StateType, Callable[[], _StateType]],
    should_update: Callable[[_StateType, _StateType], bool],
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    hook = current_hook()
    state: Dict[str, Any] = hook.use_state(dict)
    update = hook.use_update()

    if "value" not in state:
        if callable(value):
            state["value"] = value()
        else:
            state["value"] = value

    # old should be the value at the time the hook was run
    old = state["value"]

    def set_state(new: _StateType) -> None:
        if should_update(new, old):
            state["value"] = new
            update()

    return state["value"], set_state


class Ref(Generic[_StateType]):

    __slots__ = "current"

    def __init__(self, value: _StateType) -> None:
        self.current = value


def use_ref(value: _StateType) -> Ref[_StateType]:
    return use_state(Ref(value))[0]


_EffectCoro = Callable[[], Awaitable[None]]
_EffectFunc = Callable[[Callable[..., None]], None]
_Effect = TypeVar("_Effect", bound=Union[_EffectCoro, _EffectFunc])


def use_effect(function: _Effect) -> _Effect:
    hook = current_hook()

    if inspect.iscoroutinefunction(function):

        def effect() -> None:
            future = asyncio.ensure_future(function())
            hook.use_effect(future.cancel, "will_render", "will_unmount")

    else:

        def effect() -> None:
            def clean(_function_, *args, **kwargs):
                hook.use_effect(
                    lambda: _function_(*args, **kwargs), "will_render", "will_unmount"
                )

            function(clean)

    hook.use_effect(effect, "did_render")

    return function


_ActionType = TypeVar("_ActionType")


def use_reducer(
    reducer: Callable[[_StateType, _ActionType], _StateType], state: _StateType,
) -> Tuple[_StateType, Callable[[_ActionType], None]]:
    state, set_state = use_state(state)

    def dispatch(action: _ActionType) -> None:
        set_state(reducer(state, action))

    return state, dispatch


_MemoValue = TypeVar("_MemoValue")


def use_memo(*dependencies: Any) -> Callable[[Callable[[], _MemoValue]], _MemoValue]:
    def use_setup(function: Callable[[], _MemoValue]) -> _MemoValue:
        hook = current_hook()
        cache: Dict[int, _MemoValue] = hook.use_state(dict)

        key = hash(dependencies)
        if key in cache:
            result = cache[key]
        else:
            cache.clear()
            result = cache[key] = function()

        return result

    return use_setup


_CallbackFunc = TypeVar("_CallbackFunc", bound=Callable[..., Any])


def use_callback(*dependencies):
    def use_setup(function: _CallbackFunc) -> _CallbackFunc:
        return use_memo(dependencies)(lambda: function)

    return use_setup


_LruFunc = TypeVar("_LruFunc")


def use_lru_cache(
    function: _LruFunc, maxsize: Optional[int] = 128, typed: bool = False
) -> _LruFunc:
    return cast(_LruFunc, current_hook().use_state(lru_cache(maxsize, typed), function))


_current_life_cycle_hook: Dict[int, "LifeCycleHook"] = {}


def current_element() -> AbstractElement:
    # this is primarilly used for testing
    return current_hook()._element


def current_hook() -> "LifeCycleHook":
    """Get the current :class:`LifeCycleHook`"""
    try:
        return _current_life_cycle_hook[get_thread_id()]
    except KeyError as error:
        msg = "No life cycle hook is active. Are you rendering in a layout?"
        raise RuntimeError(msg) from error


class _EventEffects(NamedTuple):
    will_render: List[Callable[[], Any]]
    did_render: List[Callable[[], Any]]
    will_unmount: List[Callable[[], Any]]


class LifeCycleHook:
    """Defines the life cycle of a layout element.

    Elements can request access to their own life cycle events and state, while layouts
    drive the life cycle forward by triggering events.
    """

    __slots__ = (
        "_element",
        "_schedule_render_callback",
        "_schedule_render_later",
        "_current_state_index",
        "_state",
        "_render_is_scheduled",
        "_rendered_atleast_once",
        "_is_rendering",
        "_event_effects.will_unmount",
        "_event_effects.will_render",
        "_event_effects.did_render",
        "__weakref__",
    )

    def __init__(
        self,
        element: AbstractElement,
        schedule_render: Callable[[AbstractElement], None],
    ) -> None:
        self._element = element
        self._schedule_render_callback = schedule_render
        self._schedule_render_later = False
        self._render_is_scheduled = False
        self._is_rendering = False
        self._rendered_atleast_once = False
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._event_effects = _EventEffects([], [], [])

    @property
    def element_id(self) -> str:
        return self._element.id

    def schedule_render(self) -> None:
        if self._is_rendering:
            self._schedule_render_later = True
        elif not self._render_is_scheduled:
            self._schedule_render()
        return None

    def use_state(
        self, _function_: Callable[..., _StateType], *args: Any, **kwargs: Any
    ) -> _StateType:
        if not self._rendered_atleast_once:
            # since we're not intialized yet we're just appending state
            result = _function_(*args, **kwargs)
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result

    def use_effect(self, function: Callable[[], None], *events) -> None:
        for e in events:
            getattr(self._event_effects, e).append(function)

    def element_will_render(self) -> None:
        """The element is about to render"""
        self._render_is_scheduled = False
        self._is_rendering = True

        for effect in self._event_effects.will_render:
            effect()

        self._event_effects.will_render.clear()
        self._event_effects.will_unmount.clear()

    def element_did_render(self) -> None:
        """The element completed a render"""
        for effect in self._event_effects.did_render:
            effect()
        self._event_effects.did_render.clear()

        self._is_rendering = False
        if self._schedule_render_later:
            self._schedule_render()
        self._rendered_atleast_once = True
        self._current_state_index = 0

    def element_will_unmount(self) -> None:
        """The element is about to be removed from the layout"""
        for effect in self._event_effects.will_unmount:
            effect()
        self._event_effects.will_unmount.clear()

    def set_current(self) -> None:
        """Set this hook as the active hook in this thread

        This method is called by a layout before entering the render method
        of this hook's associated element.
        """
        _current_life_cycle_hook[get_thread_id()] = self

    def unset_current(self) -> None:
        """Unset this hook as the active hook in this thread"""
        # this assertion should never fail - primarilly useful for debug
        assert _current_life_cycle_hook[get_thread_id()] is self
        del _current_life_cycle_hook[get_thread_id()]

    def _schedule_render(self) -> None:
        self._render_is_scheduled = True
        self._schedule_render_callback(self._element)
