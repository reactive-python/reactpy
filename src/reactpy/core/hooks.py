from __future__ import annotations

import asyncio
import contextlib
import inspect
from collections.abc import Callable, Coroutine, Sequence
from logging import getLogger
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

from reactpy.config import REACTPY_DEBUG
from reactpy.core._life_cycle_hook import HOOK_STACK
from reactpy.types import (
    Connection,
    Context,
    ContextProvider,
    Key,
    Location,
    State,
)
from reactpy.utils import Ref

if not TYPE_CHECKING:
    ellipsis = type(...)

if TYPE_CHECKING:
    from asgiref import typing as asgi_types


__all__ = [
    "use_async_effect",
    "use_callback",
    "use_effect",
    "use_memo",
    "use_reducer",
    "use_ref",
    "use_state",
]

logger = getLogger(__name__)

_Type = TypeVar("_Type")


@overload
def use_state(initial_value: Callable[[], _Type]) -> State[_Type]: ...


@overload
def use_state(initial_value: _Type) -> State[_Type]: ...


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

    # FIXME: Not sure why this type hint is not being inferred correctly when using pyright
    return State(current_state.value, current_state.dispatch)  # type: ignore


class _CurrentState(Generic[_Type]):
    __slots__ = "dispatch", "value"

    def __init__(
        self,
        initial_value: _Type | Callable[[], _Type],
    ) -> None:
        self.value = initial_value() if callable(initial_value) else initial_value
        hook = HOOK_STACK.current_hook()

        def dispatch(new: _Type | Callable[[_Type], _Type]) -> None:
            next_value = new(self.value) if callable(new) else new  # type: ignore
            if not strictly_equal(next_value, self.value):
                self.value = next_value
                hook.schedule_render()

        self.dispatch = dispatch


_EffectCleanFunc: TypeAlias = "Callable[[], None]"
_SyncEffectFunc: TypeAlias = "Callable[[], _EffectCleanFunc | None]"
_AsyncEffectFunc: TypeAlias = (
    "Callable[[], Coroutine[None, None, _EffectCleanFunc | None]]"
)
_EffectApplyFunc: TypeAlias = "_SyncEffectFunc | _AsyncEffectFunc"


@overload
def use_effect(
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Callable[[_EffectApplyFunc], None]: ...


@overload
def use_effect(
    function: _SyncEffectFunc,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> None: ...


def use_effect(
    function: _SyncEffectFunc | None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Callable[[_SyncEffectFunc], None] | None:
    """
    A hook that manages an synchronous side effect in a React-like component.

    This hook allows you to run a synchronous function as a side effect and
    ensures that the effect is properly cleaned up when the component is
    re-rendered or unmounted.

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

    hook = HOOK_STACK.current_hook()
    dependencies = _try_to_infer_closure_values(function, dependencies)
    memoize = use_memo(dependencies=dependencies)
    cleanup_func: Ref[_EffectCleanFunc | None] = use_ref(None)

    def decorator(func: _SyncEffectFunc) -> None:
        if inspect.iscoroutinefunction(func):
            raise TypeError(
                "`use_effect` does not support async functions. "
                "Use `use_async_effect` instead."
            )

        async def effect(stop: asyncio.Event) -> None:
            run_effect_cleanup(cleanup_func)

            # Execute the effect and store the clean-up function
            cleanup_func.current = func()

            # Wait until we get the signal to stop this effect
            await stop.wait()

            # Run the clean-up function when the effect is stopped,
            # if it hasn't been run already by a new effect
            run_effect_cleanup(cleanup_func)

        return memoize(lambda: hook.add_effect(effect))

    # Handle decorator usage
    if function:
        decorator(function)
        return None
    return decorator


@overload
def use_async_effect(
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Callable[[_EffectApplyFunc], None]: ...


@overload
def use_async_effect(
    function: _AsyncEffectFunc,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> None: ...


def use_async_effect(
    function: _AsyncEffectFunc | None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> Callable[[_AsyncEffectFunc], None] | None:
    """
    A hook that manages an asynchronous side effect in a React-like component.

    This hook allows you to run an asynchronous function as a side effect and
    ensures that the effect is properly cleaned up when the component is
    re-rendered or unmounted.

    Args:
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
    hook = HOOK_STACK.current_hook()
    dependencies = _try_to_infer_closure_values(function, dependencies)
    memoize = use_memo(dependencies=dependencies)
    cleanup_func: Ref[_EffectCleanFunc | None] = use_ref(None)
    pending_task: Ref[asyncio.Task[_EffectCleanFunc | None] | None] = use_ref(None)

    def decorator(func: _AsyncEffectFunc) -> None:
        async def effect(stop: asyncio.Event) -> None:
            # Make sure we always clean up the previous effect's resources
            if pending_task.current:
                pending_task.current.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await pending_task.current

            run_effect_cleanup(cleanup_func)

            # Execute the effect and store the clean-up function.
            # We run this in a task so it can be cancelled if the stop signal
            # is set before the effect completes.
            task = asyncio.create_task(func())
            pending_task.current = task

            # Wait for either the effect to complete or the stop signal
            stop_task = asyncio.create_task(stop.wait())
            done, _ = await asyncio.wait(
                [task, stop_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # If the effect completed first, store the cleanup function
            if task in done:
                pending_task.current = None
                with contextlib.suppress(asyncio.CancelledError):
                    cleanup_func.current = task.result()
                # Cancel the stop task since we don't need it anymore
                stop_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await stop_task
                # Now wait for the stop signal to run cleanup
                await stop.wait()
            # Stop signal came first - cancel the effect task
            else:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            # Run the clean-up function when the effect is stopped,
            # if it hasn't been run already by a new effect
            run_effect_cleanup(cleanup_func)

        return memoize(lambda: hook.add_effect(effect))

    # Handle decorator usage
    if function:
        decorator(function)
        return None
    return decorator


def use_debug_value(
    message: Any | Callable[[], Any],
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> None:
    """Log debug information when the given message changes.

    .. note::
        This hook only logs if :data:`~reactpy.config.REACTPY_DEBUG` is active.

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

    if REACTPY_DEBUG.current and old.current != new:
        old.current = new
        logger.debug(f"{HOOK_STACK.current_hook().component} {new}")


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


def use_context(context: Context[_Type]) -> _Type:
    """Get the current value for the given context type.

    See the full :ref:`Use Context` docs for more information.
    """
    hook = HOOK_STACK.current_hook()
    provider = hook.get_context_provider(context)

    if provider is None:
        # same assertions but with normal exceptions
        if not isinstance(context, FunctionType):
            raise TypeError(f"{context} is not a Context")  # nocov
        if context.__kwdefaults__ is None:
            raise TypeError(f"{context} has no 'value' kwarg")  # nocov
        if "value" not in context.__kwdefaults__:
            raise TypeError(f"{context} has no 'value' kwarg")  # nocov
        return cast(_Type, context.__kwdefaults__["value"])

    return provider.value


# backend implementations should establish this context at the root of an app
ConnectionContext: Context[Connection[Any] | None] = create_context(None)


def use_connection() -> Connection[Any]:
    """Get the current :class:`~reactpy.backend.types.Connection`."""
    conn = use_context(ConnectionContext)
    if conn is None:  # nocov
        msg = "No backend established a connection."
        raise RuntimeError(msg)
    return conn


def use_scope() -> dict[str, Any] | asgi_types.HTTPScope | asgi_types.WebSocketScope:
    """Get the current :class:`~reactpy.types.Connection`'s scope."""
    return use_connection().scope


def use_location() -> Location:
    """Get the current :class:`~reactpy.types.Connection`'s location."""
    return use_connection().location


_ActionType = TypeVar("_ActionType")


def use_reducer(
    reducer: Callable[[_Type, _ActionType], _Type],
    initial_value: _Type,
) -> tuple[_Type, Callable[[_ActionType], None]]:
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
) -> Callable[[_CallbackFunc], _CallbackFunc]: ...


@overload
def use_callback(
    function: _CallbackFunc,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _CallbackFunc: ...


def use_callback(
    function: _CallbackFunc | None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _CallbackFunc | Callable[[_CallbackFunc], _CallbackFunc]:
    """See the full :ref:`Use Callback` docs for details

    Parameters:
        function:
            The function whose identity will be preserved
        dependencies:
            Dependencies of the callback. The identity the ``function`` will be updated
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

    return setup(function) if function is not None else setup


class _LambdaCaller(Protocol):
    """MyPy doesn't know how to deal with TypeVars only used in function return"""

    def __call__(self, func: Callable[[], _Type]) -> _Type: ...


@overload
def use_memo(
    function: None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _LambdaCaller: ...


@overload
def use_memo(
    function: Callable[[], _Type],
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _Type: ...


def use_memo(
    function: Callable[[], _Type] | None = None,
    dependencies: Sequence[Any] | ellipsis | None = ...,
) -> _Type | Callable[[Callable[[], _Type]], _Type]:
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
            for current, new in zip(memo.deps, dependencies, strict=False)
        )
    ):
        memo.deps = dependencies
        changed = True
    else:
        changed = False

    if changed:

        def setup(function: Callable[[], _Type]) -> _Type:
            current_value = memo.value = function()
            return current_value

    else:

        def setup(function: Callable[[], _Type]) -> _Type:
            return memo.value

    return setup(function) if function is not None else setup


class _Memo(Generic[_Type]):
    """Simple object for storing memoization data"""

    __slots__ = "deps", "value"

    value: _Type
    deps: Sequence[Any]

    def empty(self) -> bool:
        try:
            self.value  # noqa: B018
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
    return HOOK_STACK.current_hook().use_state(function)


def _try_to_infer_closure_values(
    func: Callable[..., Any] | None,
    values: Sequence[Any] | ellipsis | None,
) -> Sequence[Any] | None:
    if values is not ...:
        return values
    if isinstance(func, FunctionType):
        return (
            [cell.cell_contents for cell in func.__closure__]
            if func.__closure__
            else []
        )
    else:
        return None


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
    # Return early if the objects are not the same type
    if type(x) is not type(y):
        return False

    # Compare the source code of lambda and local functions
    if (
        hasattr(x, "__qualname__")
        and ("<lambda>" in x.__qualname__ or "<locals>" in x.__qualname__)
        and hasattr(x, "__code__")
    ):
        if x.__qualname__ != y.__qualname__:
            return False

        return all(
            getattr(x.__code__, attr) == getattr(y.__code__, attr)
            for attr in dir(x.__code__)
            if attr.startswith("co_")
            and attr
            not in {
                "co_positions",
                "co_linetable",
                "co_lines",
                "co_lnotab",
                "co_branches",
                "co_firstlineno",
                "co_end_lineno",
                "co_col_offset",
                "co_end_col_offset",
            }
        )

    # Check via the `==` operator if possible
    if hasattr(x, "__eq__"):
        with contextlib.suppress(Exception):
            return x == y  # type: ignore

    # Fallback to identity check
    return x is y  # nocov


def run_effect_cleanup(cleanup_func: Ref[_EffectCleanFunc | None]) -> None:
    if cleanup_func.current:
        cleanup_func.current()
        cleanup_func.current = None
