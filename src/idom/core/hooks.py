from __future__ import annotations

import asyncio
from logging import getLogger
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
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

from idom.config import IDOM_DEBUG_MODE
from idom.utils import Ref

from ._thread_local import ThreadLocal
from .types import ComponentType, Key, State, VdomDict
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

_Type = TypeVar("_Type")


@overload
def use_state(initial_value: Callable[[], _Type]) -> State[_Type]:
    ...


@overload
def use_state(initial_value: _Type) -> State[_Type]:
    ...


def use_state(initial_value: _Type | Callable[[], _Type]) -> State[_Type]:
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
    return State(current_state.value, current_state.dispatch)


class _CurrentState(Generic[_Type]):

    __slots__ = "value", "dispatch"

    def __init__(
        self,
        initial_value: Union[_Type, Callable[[], _Type]],
    ) -> None:
        if callable(initial_value):
            self.value = initial_value()
        else:
            self.value = initial_value

        hook = current_hook()

        def dispatch(new: Union[_Type, Callable[[_Type], _Type]]) -> None:
            if callable(new):
                next_value = new(self.value)
            else:
                next_value = new
            if not strictly_equal(next_value, self.value):
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


def use_debug_value(
    message: Any | Callable[[], Any],
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> None:
    """Log debug information when the given message changes.

    .. note::
        This hook only logs if :data:`~idom.config.IDOM_DEBUG_MODE` is active.

    Unlike other hooks, a message is considered to have changed if the old and new
    values are ``!=``. Because this comparison is performed on every render of the
    component, it may be worth considering the performance cost in some situations.

    Parameters:
        message:
            The value to log or a memoized function for generating the value.
        dependencies:
            Dependencies for the memoized function. The message will only be recomputed
            if the identity of any value in the given sequence changes (i.e. their
            :func:`id` is different). By default these are inferred based on local
            variables that are referenced by the given function.
    """
    old: Ref[Any] = _use_const(lambda: Ref(object()))
    memo_func = message if callable(message) else lambda: message
    new = use_memo(memo_func, dependencies)

    if IDOM_DEBUG_MODE.current and old.current != new:
        old.current = new
        logger.debug(f"{current_hook().component} {new}")


def create_context(default_value: _Type) -> Context[_Type]:
    """Return a new context type for use in :func:`use_context`"""

    def context(
        *children: Any,
        value: _Type = default_value,
        key: Key | None = None,
    ) -> ContextProvider[_Type]:
        return ContextProvider(
            *children,
            value=value,
            key=key,
            type=context,
        )

    context.__qualname__ = "context"

    return context


class Context(Protocol[_Type]):
    """Returns a :class:`ContextProvider` component"""

    def __call__(
        self,
        *children: Any,
        value: _Type = ...,
        key: Key | None = ...,
    ) -> ContextProvider[_Type]:
        ...


def use_context(context: Context[_Type]) -> _Type:
    """Get the current value for the given context type.

    See the full :ref:`Use Context` docs for more information.
    """
    hook = current_hook()
    provider = hook.get_context_provider(context)

    if provider is None:
        # force type checker to realize this is just a normal function
        assert isinstance(context, FunctionType), f"{context} is not a Context"
        # __kwdefault__ can be None if no kwarg only parameters exist
        assert context.__kwdefaults__ is not None, f"{context} has no 'value' kwarg"
        # lastly check that 'value' kwarg exists
        assert "value" in context.__kwdefaults__, f"{context} has no 'value' kwarg"
        # then we can safely access the context's default value
        return cast(_Type, context.__kwdefaults__["value"])

    subscribers = provider._subscribers

    @use_effect
    def subscribe_to_context_change() -> Callable[[], None]:
        subscribers.add(hook)
        return lambda: subscribers.remove(hook)

    return provider._value


class ContextProvider(Generic[_Type]):
    def __init__(
        self,
        *children: Any,
        value: _Type,
        key: Key | None,
        type: Context[_Type],
    ) -> None:
        self.children = children
        self.key = key
        self.type = type
        self._subscribers: set[LifeCycleHook] = set()
        self._value = value

    def render(self) -> VdomDict:
        current_hook().set_context_provider(self)
        return vdom("", *self.children)

    def should_render(self, new: ContextProvider[_Type]) -> bool:
        if not strictly_equal(self._value, new._value):
            for hook in self._subscribers:
                hook.set_context_provider(new)
                hook.schedule_render()
            return True
        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.type})"


_ActionType = TypeVar("_ActionType")


def use_reducer(
    reducer: Callable[[_Type, _ActionType], _Type],
    initial_value: _Type,
) -> Tuple[_Type, Callable[[_ActionType], None]]:
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
    reducer: Callable[[_Type, _ActionType], _Type],
    set_state: Callable[[Callable[[_Type], _Type]], None],
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

    def __call__(self, func: Callable[[], _Type]) -> _Type:
        ...


@overload
def use_memo(
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _LambdaCaller:
    ...


@overload
def use_memo(
    function: Callable[[], _Type],
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _Type:
    ...


def use_memo(
    function: Optional[Callable[[], _Type]] = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Union[_Type, Callable[[Callable[[], _Type]], _Type]]:
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

    memo: _Memo[_Type] = _use_const(_Memo)

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
        or not all(
            strictly_equal(current, new)
            for current, new in zip(memo.deps, dependencies)
        )
    ):
        memo.deps = dependencies
        changed = True
    else:
        changed = False

    setup: Callable[[Callable[[], _Type]], _Type]

    if changed:

        def setup(function: Callable[[], _Type]) -> _Type:
            current_value = memo.value = function()
            return current_value

    else:

        def setup(function: Callable[[], _Type]) -> _Type:
            return memo.value

    if function is not None:
        return setup(function)
    else:
        return setup


class _Memo(Generic[_Type]):
    """Simple object for storing memoization data"""

    __slots__ = "value", "deps"

    value: _Type
    deps: Sequence[Any]

    def empty(self) -> bool:
        try:
            self.value
        except AttributeError:
            return True
        else:
            return False


def use_ref(initial_value: _Type) -> Ref[_Type]:
    """See the full :ref:`Use State` docs for details

    Parameters:
        initial_value: The value initially assigned to the reference.

    Returns:
        A :class:`Ref` object.
    """
    return _use_const(lambda: Ref(initial_value))


def _use_const(function: Callable[[], _Type]) -> _Type:
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
        return values


def current_hook() -> LifeCycleHook:
    """Get the current :class:`LifeCycleHook`"""
    hook_stack = _hook_stack.get()
    if not hook_stack:
        msg = "No life cycle hook is active. Are you rendering in a layout?"
        raise RuntimeError(msg)
    return hook_stack[-1]


_hook_stack: ThreadLocal[list[LifeCycleHook]] = ThreadLocal(list)


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

            hook.affect_component_will_render(...)

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

            # This should only be called after the full set of changes associated with a
            # given render have been completed.
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
        "__weakref__",
        "_context_providers",
        "_current_state_index",
        "_event_effects",
        "_is_rendering",
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
        self._context_providers: dict[Context[Any], ContextProvider[Any]] = {}
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

    def use_state(self, function: Callable[[], _Type]) -> _Type:
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

    def set_context_provider(self, provider: ContextProvider[Any]) -> None:
        self._context_providers[provider.type] = provider

    def get_context_provider(
        self, context: Context[_Type]
    ) -> ContextProvider[_Type] | None:
        return self._context_providers.get(context)

    def affect_component_will_render(self, component: ComponentType) -> None:
        """The component is about to render"""
        self.component = component

        self._is_rendering = True
        self._event_effects[COMPONENT_WILL_UNMOUNT_EFFECT].clear()

    def affect_component_did_render(self) -> None:
        """The component completed a render"""
        del self.component

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
        hook_stack = _hook_stack.get()
        if hook_stack:
            parent = hook_stack[-1]
            self._context_providers.update(parent._context_providers)
        hook_stack.append(self)

    def unset_current(self) -> None:
        """Unset this hook as the active hook in this thread"""
        # this assertion should never fail - primarilly useful for debug
        assert _hook_stack.get().pop() is self

    def _schedule_render(self) -> None:
        try:
            self._schedule_render_callback()
        except Exception:
            logger.exception(
                f"Failed to schedule render via {self._schedule_render_callback}"
            )


def strictly_equal(x: Any, y: Any) -> bool:
    """Check if two values are identical or, for a limited set or types, equal.

    Only the following types are checked for equality rather than identity:

    - ``int``
    - ``float``
    - ``complex``
    - ``str``
    - ``bytes``
    - ``bytearray``
    - ``memoryview``
    """
    return x is y or (type(x) in _NUMERIC_TEXT_BINARY_TYPES and x == y)


_NUMERIC_TEXT_BINARY_TYPES = {
    # numeric
    int,
    float,
    complex,
    # text
    str,
    # binary types
    bytes,
    bytearray,
    memoryview,
}
