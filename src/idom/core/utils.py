import sys
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import AsyncExitStack, asynccontextmanager  # noqa
else:  # pragma: no cover
    from async_exit_stack import AsyncExitStack
    from async_generator import asynccontextmanager


def hex_id(obj: Any) -> str:
    return format(id(obj), "x")


_Rsrc = TypeVar("_Rsrc")
_Self = TypeVar("_Self", bound="HasAsyncResources")


def async_resource(
    method: Callable[[Any], AsyncIterator[_Rsrc]]
) -> "AsyncResource[_Rsrc]":
    """A decorator for creating an :class:`AsyncResource`"""
    return AsyncResource(method)


class CannotAccessResource(RuntimeError):
    """When a resource of :class:`HasAsyncResources` object is incorrectly accessed"""


class HasAsyncResources:

    _async_resource_names: Tuple[str, ...] = ()
    __slots__ = "_async_resource_state", "_async_exit_stack"

    def __init__(self) -> None:
        self._async_resource_state: Dict[str, Any] = {}
        self._async_exit_stack: Optional[AsyncExitStack] = None

    def __init_subclass__(cls: Type["HasAsyncResources"]) -> None:
        for k, v in list(cls.__dict__.items()):
            if isinstance(v, AsyncResource) and k not in cls._async_resource_names:
                cls._async_resource_names += (k,)
        return None

    async def __aenter__(self: _Self) -> _Self:
        if self._async_exit_stack is not None:
            raise CannotAccessResource(f"{self} is already open")

        self._async_exit_stack = await AsyncExitStack().__aenter__()

        for rsrc_name in self._async_resource_names:
            rsrc: AsyncResource[Any] = getattr(type(self), rsrc_name)
            await self._async_exit_stack.enter_async_context(rsrc.context(self))

        return self

    async def __aexit__(self, *exc: Any) -> bool:
        if self._async_exit_stack is None:
            raise CannotAccessResource(f"{self} is not open")

        result = await self._async_exit_stack.__aexit__(*exc)
        self._async_exit_stack = None
        return result


class AsyncResource(Generic[_Rsrc]):

    __slots__ = "_context_manager", "_name"

    def __init__(
        self,
        method: Callable[[Any], AsyncIterator[_Rsrc]],
    ) -> None:
        self._context_manager = asynccontextmanager(method)

    @asynccontextmanager
    async def context(self, obj: HasAsyncResources) -> AsyncIterator[None]:
        try:
            async with self._context_manager(obj) as value:
                obj._async_resource_state[self._name] = value
                yield None
        finally:
            if self._name in obj._async_resource_state:
                del obj._async_resource_state[self._name]

    def __set_name__(self, cls: Type[HasAsyncResources], name: str) -> None:
        self._name = name

    @overload
    def __get__(
        self, obj: None, cls: Type[HasAsyncResources]
    ) -> "AsyncResource[_Rsrc]":
        ...

    @overload
    def __get__(self, obj: HasAsyncResources, cls: Type[HasAsyncResources]) -> _Rsrc:
        ...

    def __get__(
        self, obj: Optional[HasAsyncResources], cls: Type[HasAsyncResources]
    ) -> Union[_Rsrc, "AsyncResource[_Rsrc]"]:
        if obj is None:
            return self
        else:
            try:
                return cast(_Rsrc, obj._async_resource_state[self._name])
            except KeyError:
                raise CannotAccessResource(
                    f"Resource {self._name!r} of {obj} is not open"
                )
