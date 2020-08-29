from threading import get_ident as get_thread_id
from typing import (
    Sequence,
    Dict,
    Any,
    TypeVar,
    Callable,
    Tuple,
    Optional,
    Generic,
    Union,
    NamedTuple,
    List,
    overload,
)

from .element import AbstractElement


__all__ = [
    "use_state",
    "use_effect",
    "use_ref",
    "use_memo",
    "use_callback",
]


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
                next_value = new(self.current)
            else:
                next_value = new
            if next_value is not self.value:
                self.value = next_value
                hook.schedule_render()

        self.dispatch = dispatch


_EffectCleanFunc = Callable[[], None]
_EffectApplyFunc = Callable[[], Optional[_EffectCleanFunc]]


@overload
def use_effect(
    function: None, args: Optional[Sequence[Any]]
) -> Callable[[_EffectApplyFunc], None]:
    ...


@overload
def use_effect(function: _EffectApplyFunc, args: Optional[Sequence[Any]]) -> None:
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

    def setup(function: _EffectApplyFunc) -> None:
        def effect() -> None:
            clean = function()
            if clean is not None:
                hook.add_effect("will_render will_unmount", clean)

        return memoize(lambda: hook.add_effect("did_render", effect))

    if function is not None:
        return setup(function)
    else:
        return setup


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
    set_state: Callable[[_StateType], None],
) -> Callable[[_ActionType], None]:
    def dispatch(action: _ActionType) -> None:
        set_state(lambda last_state: reducer(last_state, action))

    return dispatch


_CallbackFunc = TypeVar("_CallbackFunc", bound=Callable[..., Any])


@overload
def use_callback(
    function: None, args: Optional[Sequence[Any]]
) -> Callable[[_CallbackFunc], None]:
    ...


@overload
def use_callback(function: _CallbackFunc, args: Optional[Sequence[Any]]) -> None:
    ...


def use_callback(
    function: Optional[_CallbackFunc] = None,
    args: Optional[Sequence[Any]] = None,
) -> Optional[Callable[[_CallbackFunc], None]]:
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


_MemoValue = TypeVar("_MemoValue")


@overload
def use_memo(
    function: None, args: Optional[Sequence[Any]]
) -> Callable[[Callable[[], _MemoValue]], _MemoValue]:
    ...


@overload
def use_memo(
    function: Callable[[], _MemoValue], args: Optional[Sequence[Any]]
) -> _MemoValue:
    ...


def use_memo(
    function: Optional[Callable[[], _MemoValue]] = None,
    args: Optional[Sequence[Any]] = None,
) -> Union[_MemoValue, Callable[[Callable[[], _MemoValue]], _MemoValue]]:
    """See the full :ref:`use_memo` docs for details

    Parameters:
        function: The function to be memoized.
        args: The ``function`` will be recomputed when these args change.

    Returns:
        The current state
    """
    args_ref = use_ref(None)
    value_ref: Ref[_MemoValue] = _use_const(Ref)

    try:
        value_ref.current
    except AttributeError:
        changed = True
    else:
        if (
            args is None
            or len(args_ref.current) != args
            or any(current is not new for current, new in zip(args_ref.current, args))
        ):
            args_ref.current = args
            changed = True
        else:
            changed = False

    if changed:

        def setup(function: Callable[[], _MemoValue]) -> _MemoValue:
            current_value = value_ref.current = function()
            return current_value

    else:

        def setup(function: Callable[[], _MemoValue]) -> _MemoValue:
            return value_ref.current

    if function is not None:
        return setup(function)
    else:
        return setup


class Ref(Generic[_StateType]):
    """Hold a reference to a value

    This is used in imperative code to mutate the state of this object in order to
    incur side effects. Generally refs should be avoided if possible, but sometimes
    they are required.

    The constructor for a :class:`Ref` does not accept any arguments. To initialize a
    :class:`Ref` with a starting value use the :meth:`Ref.init` method.
    """

    __slots__ = "current"

    current: _StateType
    """The value currently assigned to the reference"""

    @classmethod
    def init(cls, value):
        """Return a reference with an initial value"""
        ref = cls()
        ref.current = value
        return ref


def use_ref(initial_value: _StateType) -> Ref[_StateType]:
    """See the full :ref:`use_state` docs for details

    Parameters:
        initial_value: The value initially assigned to the reference.

    Returns:
        A :class:`Ref` object.
    """
    return _use_const(lambda: Ref.init(initial_value))


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
    will_render: List[Callable[[], Any]]
    did_render: List[Callable[[], Any]]
    will_unmount: List[Callable[[], Any]]


class LifeCycleHook:
    """Defines the life cycle of a layout element.

    Elements can request access to their own life cycle events and state, while layouts
    drive the life cycle forward by triggering events.
    """

    __slots__ = (
        "element",
        "_schedule_render_callback",
        "_schedule_render_later",
        "_current_state_index",
        "_state",
        "_render_is_scheduled",
        "_rendered_atleast_once",
        "_is_rendering",
        "_event_effects",
        "__weakref__",
    )

    def __init__(
        self,
        element: AbstractElement,
        schedule_render: Callable[[AbstractElement], None],
    ) -> None:
        self.element = element
        self._schedule_render_callback = schedule_render
        self._schedule_render_later = False
        self._render_is_scheduled = False
        self._is_rendering = False
        self._rendered_atleast_once = False
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._event_effects = _EventEffects([], [], [])

    def schedule_render(self) -> None:
        if self._is_rendering:
            self._schedule_render_later = True
        elif not self._render_is_scheduled:
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
        self._schedule_render_callback(self.element)
