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
    "use_update",
    "use_state",
    "use_effect",
    "use_ref",
    "use_memo",
    "use_callback",
]


def use_update() -> Callable[[], None]:
    return current_hook().schedule_render


_StateType = TypeVar("_StateType")


class _State:
    __slots__ = "current"


def use_state(
    value: Union[_StateType, Callable[[], _StateType]],
) -> Tuple[
    _StateType, Callable[[Union[_StateType, Callable[[_StateType], _StateType]]], None]
]:
    hook = current_hook()
    state: Dict[str, Any] = hook.use_state(_State)
    update = use_update()

    try:
        current = state.current
    except AttributeError:
        if callable(value):
            current = state.current = value()
        else:
            current = state.current = value

    def set_state(new: Union[_StateType, Callable[[_StateType], _StateType]]) -> None:
        if callable(new):
            next_state = new(current)
        else:
            next_state = new
        if next_state is not current:
            state.current = next_state
            update()

    return current, set_state


class Ref(Generic[_StateType]):
    """Hold a reference to a value

    This is used in imperative code to mutate the state of this object in order to
    incur side effects. Generally refs should be avoided if possible, but sometimes
    they are required.

    The constructor for a :class:`Ref` does not accept any arguments. To initialize one
    with a starting value use the :meth:`Ref.init` method.
    """

    __slots__ = "current"

    current: _StateType

    @classmethod
    def init(cls, value):
        ref = cls()
        ref.current = value
        return ref


def use_ref(value: _StateType) -> Ref[_StateType]:
    return use_state(lambda: Ref.init(value))[0]


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
    state: _StateType,
) -> Tuple[_StateType, Callable[[_ActionType], None]]:
    state, set_state = use_state(state)

    def dispatch(action: _ActionType) -> None:
        set_state(reducer(state, action))

    return state, dispatch


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
    args_ref = use_ref(None)
    value_ref: Ref[_MemoValue] = use_state(Ref)

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
    memoize = use_memo(args=args)

    def setup(function: _CallbackFunc) -> _CallbackFunc:
        return memoize(lambda: function)

    if function is not None:
        return setup(function)
    else:
        return setup


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
