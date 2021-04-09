from __future__ import annotations

import asyncio
import weakref
from logging import getLogger
from threading import get_ident as get_thread_id
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from typing_extensions import Protocol

import idom
from idom.utils import Ref

from .component import AbstractComponent


__all__ = [
    "use_state",
    "use_effect",
    "use_reducer",
    "use_callback",
    "use_ref",
    "use_memo",
]

logger = getLogger(__name__)

_StateType = TypeVar("_StateType")


def use_state(
    initial_value: Union[_StateType, Callable[[], _StateType]],
) -> Tuple[
    _StateType, Callable[[Union[_StateType, Callable[[_StateType], _StateType]]], None]
]:
    """See the full :ref:`use_state` docs for details

    Parameters:
        initial_value:
            Defines the initial value of the state. A callable (accepting no arguments)
            can be used as a constructor function to avoid re-creating the initial value
            on each render.

    Returns:
        A tuple containing the current state and a function to update it.
    """
    current_state = _use_const(lambda: _CurrentState(initial_value))
    return current_state.value, current_state.dispatch


class _CurrentState(Generic[_StateType]):

    __slots__ = "value", "dispatch"

    def __init__(
        self,
        initial_value: Union[_StateType, Callable[[], _StateType]],
    ) -> None:
        if callable(initial_value):
            self.value = initial_value()
        else:
            self.value = initial_value

        hook = current_hook()

        def dispatch(
            new: Union[_StateType, Callable[[_StateType], _StateType]]
        ) -> None:
            if callable(new):
                next_value = new(self.value)
            else:
                next_value = new
            if next_value is not self.value:
                self.value = next_value
                hook.schedule_render()

        self.dispatch = dispatch


_EffectCleanFunc = Callable[[], None]
_SyncEffectFunc = Callable[[], Optional[_EffectCleanFunc]]
_AsyncEffectFunc = Callable[[], Awaitable[Optional[_EffectCleanFunc]]]
_EffectApplyFunc = Union[_SyncEffectFunc, _AsyncEffectFunc]


@overload
def use_effect(
    function: None = None, args: Optional[Sequence[Any]] = None
) -> Callable[[_EffectApplyFunc], None]:
    ...


@overload
def use_effect(
    function: _EffectApplyFunc, args: Optional[Sequence[Any]] = None
) -> None:
    ...


def use_effect(
    function: Optional[_EffectApplyFunc] = None,
    args: Optional[Sequence[Any]] = None,
) -> Optional[Callable[[_EffectApplyFunc], None]]:
    """See the full :ref:`use_effect` docs for details

    Parameters:
        function:
            Applies the effect and can return a clean-up function
        args:
            Dependencies for the effect. If provided the effect will only trigger when
            these args change.

    Returns:
        If not function is provided, a decorator. Otherwise ``None``.
    """
    hook = current_hook()
    memoize = use_memo(args=args)
    last_clean_callback: Ref[Optional[_EffectCleanFunc]] = use_ref(None)

    def add_effect(function: _EffectApplyFunc) -> None:

        if not asyncio.iscoroutinefunction(function):
            sync_function = cast(_SyncEffectFunc, function)
        else:

            async_function = cast(_AsyncEffectFunc, function)

            def sync_function() -> Optional[_EffectCleanFunc]:
                future = asyncio.ensure_future(async_function())

                def clean_future() -> None:
                    if not future.cancel():
                        clean = future.result()
                        if clean is not None:
                            clean()

                return clean_future

        def effect() -> None:
            if last_clean_callback.current is not None:
                last_clean_callback.current()

            clean = last_clean_callback.current = sync_function()
            if clean is not None:
                hook.add_effect("will_unmount", clean)

            return None

        return memoize(lambda: hook.add_effect("did_render", effect))

    if function is not None:
        add_effect(function)
        return None
    else:
        return add_effect


_ActionType = TypeVar("_ActionType")


def use_reducer(
    reducer: Callable[[_StateType, _ActionType], _StateType],
    initial_value: _StateType,
) -> Tuple[_StateType, Callable[[_ActionType], None]]:
    """See the full :ref:`use_reducer` docs for details

    Parameters:
        reducer:
            A function which applies an action to the current state in order to
            produce the next state.
        initial_value:
            The initial state value (same as for :func:`use_state`)

    Returns:
        A tuple containing the current state and a function to change it with an action
    """
    state, set_state = use_state(initial_value)
    return state, _use_const(lambda: _create_dispatcher(reducer, set_state))


def _create_dispatcher(
    reducer: Callable[[_StateType, _ActionType], _StateType],
    set_state: Callable[[Callable[[_StateType], _StateType]], None],
) -> Callable[[_ActionType], None]:
    def dispatch(action: _ActionType) -> None:
        set_state(lambda last_state: reducer(last_state, action))

    return dispatch


_CallbackFunc = TypeVar("_CallbackFunc", bound=Callable[..., Any])


@overload
def use_callback(
    function: None = None, args: Optional[Sequence[Any]] = None
) -> Callable[[_CallbackFunc], _CallbackFunc]:
    ...


@overload
def use_callback(
    function: _CallbackFunc, args: Optional[Sequence[Any]] = None
) -> _CallbackFunc:
    ...


def use_callback(
    function: Optional[_CallbackFunc] = None,
    args: Optional[Sequence[Any]] = (),
) -> Union[_CallbackFunc, Callable[[_CallbackFunc], _CallbackFunc]]:
    """See the full :ref:`use_callback` docs for details

    Parameters:
        function: the function whose identity will be preserved
        args: The identity the ``function`` will be udpated when these ``args`` change.

    Returns:
        The current function
    """
    memoize = use_memo(args=args)

    def setup(function: _CallbackFunc) -> _CallbackFunc:
        return memoize(lambda: function)

    if function is not None:
        return setup(function)
    else:
        return setup


class _LambdaCaller(Protocol):
    """MyPy doesn't know how to deal with TypeVars only used in function return"""

    def __call__(self, func: Callable[[], _StateType]) -> _StateType:
        ...


@overload
def use_memo(
    function: None = None, args: Optional[Sequence[Any]] = None
) -> _LambdaCaller:
    ...


@overload
def use_memo(
    function: Callable[[], _StateType], args: Optional[Sequence[Any]] = None
) -> _StateType:
    ...


def use_memo(
    function: Optional[Callable[[], _StateType]] = None,
    args: Optional[Sequence[Any]] = None,
) -> Union[_StateType, Callable[[Callable[[], _StateType]], _StateType]]:
    """See the full :ref:`use_memo` docs for details

    Parameters:
        function: The function to be memoized.
        args: The ``function`` will be recomputed when these args change.

    Returns:
        The current state
    """
    memo: _Memo[_StateType] = _use_const(_Memo)

    if memo.empty():
        # we need to initialize on the first run
        changed = True
        memo.args = () if args is None else args
    elif args is None:
        changed = True
        memo.args = ()
    elif (
        len(memo.args) != len(args)
        # if args are same length check identity for each item
        or any(current is not new for current, new in zip(memo.args, args))
    ):
        memo.args = args
        changed = True
    else:
        changed = False

    setup: Callable[[Callable[[], _StateType]], _StateType]

    if changed:

        def setup(function: Callable[[], _StateType]) -> _StateType:
            current_value = memo.value = function()
            return current_value

    else:

        def setup(function: Callable[[], _StateType]) -> _StateType:
            return memo.value

    if function is not None:
        return setup(function)
    else:
        return setup


class _Memo(Generic[_StateType]):
    """Simple object for storing memoization data"""

    __slots__ = "value", "args"

    value: _StateType
    args: Sequence[Any]

    def empty(self) -> bool:
        try:
            self.value
        except AttributeError:
            return True
        else:
            return False


def use_ref(initial_value: _StateType) -> Ref[_StateType]:
    """See the full :ref:`use_state` docs for details

    Parameters:
        initial_value: The value initially assigned to the reference.

    Returns:
        A :class:`Ref` object.
    """
    return _use_const(lambda: Ref(initial_value))


def _use_const(function: Callable[[], _StateType]) -> _StateType:
    return current_hook().use_state(function)


_current_life_cycle_hook: Dict[int, "LifeCycleHook"] = {}


def current_hook() -> "LifeCycleHook":
    """Get the current :class:`LifeCycleHook`"""
    try:
        return _current_life_cycle_hook[get_thread_id()]
    except KeyError as error:
        msg = "No life cycle hook is active. Are you rendering in a layout?"
        raise RuntimeError(msg) from error


class _EventEffects(NamedTuple):
    did_render: List[Callable[[], Any]]
    will_unmount: List[Callable[[], Any]]


class LifeCycleHook:
    """Defines the life cycle of a layout component.

    Components can request access to their own life cycle events and state, while layouts
    drive the life cycle forward by triggering events.
    """

    __slots__ = (
        "component",
        "_layout",
        "_schedule_render_later",
        "_current_state_index",
        "_state",
        "_rendered_atleast_once",
        "_is_rendering",
        "_event_effects",
        "__weakref__",
    )

    def __init__(
        self,
        component: AbstractComponent,
        layout: idom.core.layout.Layout,
    ) -> None:
        self.component = component
        self._layout = weakref.ref(layout)
        self._schedule_render_later = False
        self._is_rendering = False
        self._rendered_atleast_once = False
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._event_effects = _EventEffects([], [])

    def schedule_render(self) -> None:
        if self._is_rendering:
            self._schedule_render_later = True
        else:
            self._schedule_render()
        return None

    def use_state(self, function: Callable[[], _StateType]) -> _StateType:
        if not self._rendered_atleast_once:
            # since we're not intialized yet we're just appending state
            result = function()
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result

    def add_effect(self, events: str, function: Callable[[], None]) -> None:
        for e in events.split():
            getattr(self._event_effects, e).append(function)

    def component_will_render(self) -> None:
        """The component is about to render"""
        self._is_rendering = True
        self._event_effects.will_unmount.clear()

    def component_did_render(self) -> None:
        """The component completed a render"""
        for effect in self._event_effects.did_render:
            try:
                effect()
            except Exception:
                msg = f"Post-render effect {effect} failed for {self.component}"
                logger.exception(msg)

        self._event_effects.did_render.clear()

        self._is_rendering = False
        if self._schedule_render_later:
            self._schedule_render()
        self._rendered_atleast_once = True
        self._current_state_index = 0

    def component_will_unmount(self) -> None:
        """The component is about to be removed from the layout"""
        for effect in self._event_effects.will_unmount:
            try:
                effect()
            except Exception:
                msg = f"Pre-unmount effect {effect} failed for {self.component}"
                logger.exception(msg)

        self._event_effects.will_unmount.clear()

    def set_current(self) -> None:
        """Set this hook as the active hook in this thread

        This method is called by a layout before entering the render method
        of this hook's associated component.
        """
        _current_life_cycle_hook[get_thread_id()] = self

    def unset_current(self) -> None:
        """Unset this hook as the active hook in this thread"""
        # this assertion should never fail - primarilly useful for debug
        assert _current_life_cycle_hook[get_thread_id()] is self
        del _current_life_cycle_hook[get_thread_id()]

    def _schedule_render(self) -> None:
        layout = self._layout()
        assert layout is not None
        layout.update(self.component)
