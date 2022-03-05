from __future__ import annotations

import asyncio
from logging import getLogger
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    NewType,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from typing_extensions import Protocol

from idom.utils import Ref

from ._thread_local import ThreadLocal
from .types import Key, VdomDict
from .vdom import vdom


if not TYPE_CHECKING:
    # make flake8 think that this variable exists
    ellipsis = type(...)


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


@overload
def use_state(
    initial_value: Callable[[], _StateType],
) -> Tuple[
    _StateType,
    Callable[[_StateType | Callable[[_StateType], _StateType]], None],
]:
    ...


@overload
def use_state(
    initial_value: _StateType,
) -> Tuple[
    _StateType,
    Callable[[_StateType | Callable[[_StateType], _StateType]], None],
]:
    ...


def use_state(
    initial_value: _StateType | Callable[[], _StateType],
) -> Tuple[
    _StateType,
    Callable[[_StateType | Callable[[_StateType], _StateType]], None],
]:
    """See the full :ref:`Use State` docs for details

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
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Callable[[_EffectApplyFunc], None]:
    ...


@overload
def use_effect(
    function: _EffectApplyFunc,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> None:
    ...


def use_effect(
    function: Optional[_EffectApplyFunc] = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Optional[Callable[[_EffectApplyFunc], None]]:
    """See the full :ref:`Use Effect` docs for details

    Parameters:
        function:
            Applies the effect and can return a clean-up function
        dependencies:
            Dependencies for the effect. The effect will only trigger if the identity
            of any value in the given sequence changes (i.e. their :func:`id` is
            different). By default these are inferred based on local variables that are
            referenced by the given function.

    Returns:
        If not function is provided, a decorator. Otherwise ``None``.
    """
    hook = current_hook()

    dependencies = _try_to_infer_closure_values(function, dependencies)
    memoize = use_memo(dependencies=dependencies)
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
                hook.add_effect(COMPONENT_WILL_UNMOUNT_EFFECT, clean)

            return None

        return memoize(lambda: hook.add_effect(LAYOUT_DID_RENDER_EFFECT, effect))

    if function is not None:
        add_effect(function)
        return None
    else:
        return add_effect


def create_context(
    default_value: _StateType, name: str | None = None
) -> type[_Context[_StateType]]:
    """Return a new context type for use in :func:`use_context`"""

    class Context(_Context[_StateType]):
        _default_value = default_value

    if name is not None:
        Context.__name__ = name

    return Context


def use_context(context_type: type[_Context[_StateType]]) -> _StateType:
    """Get the current value for the given context type.

    See the full :ref:`Use Context` docs for more information.
    """
    # We have to use a Ref here since, if initially context_type._current is None, and
    # then on a subsequent render it is present, we need to be able to dynamically adopt
    # that newly present current context. When we update it though, we don't need to
    # schedule a new render since we're already rending right now. Thus we can't do this
    # with use_state() since we'd incur an extra render when calling set_state.
    context_ref: Ref[_Context[_StateType] | None] = use_ref(None)

    if context_ref.current is None:
        provided_context = context_type._current.get()
        if provided_context is None:
            # Cast required because of: https://github.com/python/mypy/issues/5144
            return cast(_StateType, context_type._default_value)
        context_ref.current = provided_context

    # We need the hook now so that we can schedule an update when
    hook = current_hook()

    context = context_ref.current

    @use_effect
    def subscribe_to_context_change() -> Callable[[], None]:
        def set_context(new: _Context[_StateType]) -> None:
            # We don't need to check if `new is not context_ref.current` because we only
            # trigger this callback when the value of a context, and thus the context
            # itself changes. Therefore we can always schedule a render.
            context_ref.current = new
            hook.schedule_render()

        context.subscribers.add(set_context)
        return lambda: context.subscribers.remove(set_context)

    return context.value


_UNDEFINED: Any = object()


class _Context(Generic[_StateType]):

    # This should be _StateType instead of Any, but it can't due to this limitation:
    # https://github.com/python/mypy/issues/5144
    _default_value: ClassVar[Any]

    _current: ClassVar[ThreadLocal[_Context[Any] | None]]

    def __init_subclass__(cls) -> None:
        # every context type tracks which of its instances are currently in use
        cls._current = ThreadLocal(lambda: None)

    def __init__(
        self,
        *children: Any,
        value: _StateType = _UNDEFINED,
        key: Key | None = None,
    ) -> None:
        self.children = children
        self.value: _StateType = self._default_value if value is _UNDEFINED else value
        self.key = key
        self.subscribers: set[Callable[[_Context[_StateType]], None]] = set()
        self.type = self.__class__

    def render(self) -> VdomDict:
        current_ctx = self.__class__._current

        prior_ctx = current_ctx.get()
        current_ctx.set(self)

        def reset_ctx() -> None:
            current_ctx.set(prior_ctx)

        current_hook().add_effect(COMPONENT_DID_RENDER_EFFECT, reset_ctx)

        return vdom("", *self.children)

    def should_render(self, new: _Context[_StateType]) -> bool:
        if self.value is not new.value:
            new.subscribers.update(self.subscribers)
            for set_context in self.subscribers:
                set_context(new)
            return True
        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({id(self)})"


_ActionType = TypeVar("_ActionType")


def use_reducer(
    reducer: Callable[[_StateType, _ActionType], _StateType],
    initial_value: _StateType,
) -> Tuple[_StateType, Callable[[_ActionType], None]]:
    """See the full :ref:`Use Reducer` docs for details

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
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Callable[[_CallbackFunc], _CallbackFunc]:
    ...


@overload
def use_callback(
    function: _CallbackFunc,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _CallbackFunc:
    ...


def use_callback(
    function: Optional[_CallbackFunc] = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Union[_CallbackFunc, Callable[[_CallbackFunc], _CallbackFunc]]:
    """See the full :ref:`Use Callback` docs for details

    Parameters:
        function:
            The function whose identity will be preserved
        dependencies:
            Dependencies of the callback. The identity the ``function`` will be udpated
            if the identity of any value in the given sequence changes (i.e. their
            :func:`id` is different). By default these are inferred based on local
            variables that are referenced by the given function.

    Returns:
        The current function
    """
    dependencies = _try_to_infer_closure_values(function, dependencies)
    memoize = use_memo(dependencies=dependencies)

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
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _LambdaCaller:
    ...


@overload
def use_memo(
    function: Callable[[], _StateType],
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _StateType:
    ...


def use_memo(
    function: Optional[Callable[[], _StateType]] = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Union[_StateType, Callable[[Callable[[], _StateType]], _StateType]]:
    """See the full :ref:`Use Memo` docs for details

    Parameters:
        function:
            The function to be memoized.
        dependencies:
            Dependencies for the memoized function. The memo will only be recomputed if
            the identity of any value in the given sequence changes (i.e. their
            :func:`id` is different). By default these are inferred based on local
            variables that are referenced by the given function.

    Returns:
        The current state
    """
    dependencies = _try_to_infer_closure_values(function, dependencies)

    memo: _Memo[_StateType] = _use_const(_Memo)

    if memo.empty():
        # we need to initialize on the first run
        changed = True
        memo.deps = () if dependencies is None else dependencies
    elif dependencies is None:
        changed = True
        memo.deps = ()
    elif (
        len(memo.deps) != len(dependencies)
        # if deps are same length check identity for each item
        or any(current is not new for current, new in zip(memo.deps, dependencies))
    ):
        memo.deps = dependencies
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

    __slots__ = "value", "deps"

    value: _StateType
    deps: Sequence[Any]

    def empty(self) -> bool:
        try:
            self.value
        except AttributeError:
            return True
        else:
            return False


def use_ref(initial_value: _StateType) -> Ref[_StateType]:
    """See the full :ref:`Use State` docs for details

    Parameters:
        initial_value: The value initially assigned to the reference.

    Returns:
        A :class:`Ref` object.
    """
    return _use_const(lambda: Ref(initial_value))


def _use_const(function: Callable[[], _StateType]) -> _StateType:
    return current_hook().use_state(function)


def _try_to_infer_closure_values(
    func: Callable[..., Any] | None,
    values: Sequence[Any] | ellipsis | None,
) -> Sequence[Any] | None:
    if values is ...:
        if isinstance(func, FunctionType):
            return (
                [cell.cell_contents for cell in func.__closure__]
                if func.__closure__
                else []
            )
        else:
            return None
    else:
        return cast("Sequence[Any] | None", values)


def current_hook() -> LifeCycleHook:
    """Get the current :class:`LifeCycleHook`"""
    hook = _current_hook.get()
    if hook is None:
        msg = "No life cycle hook is active. Are you rendering in a layout?"
        raise RuntimeError(msg)
    return hook


_current_hook: ThreadLocal[LifeCycleHook | None] = ThreadLocal(lambda: None)


EffectType = NewType("EffectType", str)
"""Used in :meth:`LifeCycleHook.add_effect` to indicate what effect should be saved"""

COMPONENT_DID_RENDER_EFFECT = EffectType("COMPONENT_DID_RENDER")
"""An effect that will be triggered each time a component renders"""

LAYOUT_DID_RENDER_EFFECT = EffectType("LAYOUT_DID_RENDER")
"""An effect that will be triggered each time a layout renders"""

COMPONENT_WILL_UNMOUNT_EFFECT = EffectType("COMPONENT_WILL_UNMOUNT")
"""An effect that will be triggered just before the component is unmounted"""


class LifeCycleHook:
    """Defines the life cycle of a layout component.

    Components can request access to their own life cycle events and state through hooks
    while :class:`~idom.core.proto.LayoutType` objects drive drive the life cycle
    forward by triggering events and rendering view changes.

    Example:

        If removed from the complexities of a layout, a very simplified full life cycle
        for a single component with no child components would look a bit like this:

        .. testcode::

            from idom.core.hooks import (
                current_hook,
                LifeCycleHook,
                COMPONENT_DID_RENDER_EFFECT,
            )


            # this function will come from a layout implementation
            schedule_render = lambda: ...

            # --- start life cycle ---

            hook = LifeCycleHook(schedule_render)

            # --- start render cycle ---

            hook.affect_component_will_render()

            hook.set_current()

            try:
                # render the component
                ...

                # the component may access the current hook
                assert current_hook() is hook

                # and save state or add effects
                current_hook().use_state(lambda: ...)
                current_hook().add_effect(COMPONENT_DID_RENDER_EFFECT, lambda: ...)
            finally:
                hook.unset_current()

            hook.affect_component_did_render()

            # This should only be called after any child components yielded by
            # component_instance.render() have also been rendered because effects of
            # this type must run after the full set of changes have been resolved.
            hook.affect_layout_did_render()

            # Typically an event occurs and a new render is scheduled, thus begining
            # the render cycle anew.
            hook.schedule_render()


            # --- end render cycle ---

            hook.affect_component_will_unmount()
            del hook

            # --- end render cycle ---
    """

    __slots__ = (
        "_schedule_render_callback",
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
        schedule_render: Callable[[], None],
    ) -> None:
        self._schedule_render_callback = schedule_render
        self._schedule_render_later = False
        self._is_rendering = False
        self._rendered_atleast_once = False
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._event_effects: Dict[EffectType, List[Callable[[], None]]] = {
            COMPONENT_DID_RENDER_EFFECT: [],
            LAYOUT_DID_RENDER_EFFECT: [],
            COMPONENT_WILL_UNMOUNT_EFFECT: [],
        }

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

    def add_effect(self, effect_type: EffectType, function: Callable[[], None]) -> None:
        """Trigger a function on the occurance of the given effect type"""
        self._event_effects[effect_type].append(function)

    def affect_component_will_render(self) -> None:
        """The component is about to render"""
        self._is_rendering = True
        self._event_effects[COMPONENT_WILL_UNMOUNT_EFFECT].clear()

    def affect_component_did_render(self) -> None:
        """The component completed a render"""
        component_did_render_effects = self._event_effects[COMPONENT_DID_RENDER_EFFECT]
        for effect in component_did_render_effects:
            try:
                effect()
            except Exception:
                logger.exception(f"Component post-render effect {effect} failed")
        component_did_render_effects.clear()

        self._is_rendering = False
        self._rendered_atleast_once = True
        self._current_state_index = 0

    def affect_layout_did_render(self) -> None:
        """The layout completed a render"""
        layout_did_render_effects = self._event_effects[LAYOUT_DID_RENDER_EFFECT]
        for effect in layout_did_render_effects:
            try:
                effect()
            except Exception:
                logger.exception(f"Layout post-render effect {effect} failed")
        layout_did_render_effects.clear()

        if self._schedule_render_later:
            self._schedule_render()
        self._schedule_render_later = False

    def affect_component_will_unmount(self) -> None:
        """The component is about to be removed from the layout"""
        will_unmount_effects = self._event_effects[COMPONENT_WILL_UNMOUNT_EFFECT]
        for effect in will_unmount_effects:
            try:
                effect()
            except Exception:
                logger.exception(f"Pre-unmount effect {effect} failed")
        will_unmount_effects.clear()

    def set_current(self) -> None:
        """Set this hook as the active hook in this thread

        This method is called by a layout before entering the render method
        of this hook's associated component.
        """
        _current_hook.set(self)

    def unset_current(self) -> None:
        """Unset this hook as the active hook in this thread"""
        # this assertion should never fail - primarilly useful for debug
        assert _current_hook.get() is self
        _current_hook.set(None)

    def _schedule_render(self) -> None:
        try:
            self._schedule_render_callback()
        except Exception:
            logger.exception(
                f"Failed to schedule render via {self._schedule_render_callback}"
            )
