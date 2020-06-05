from typing import (
    TypeVar,
    Any,
    Type,
    Callable,
    Optional,
    AsyncIterator,
    Generic,
    Union,
    Dict,
    Tuple,
    cast,
    overload,
)

try:
    from contextlib import asynccontextmanager, AbstractAsyncContextManager  # noqa
except ImportError:  # pragma: no cover
    from async_generator import asynccontextmanager  # type: ignore


_Rsrc = TypeVar("_Rsrc")
_Self = TypeVar("_Self", bound="HasAsyncResources")
_ResourceState = Dict[str, Tuple["AbstractAsyncContextManager[Any]", Any]]


def async_resource(
    method: Callable[[Any], AsyncIterator[_Rsrc]]
) -> "AsyncResource[_Rsrc]":
    """A decorator for creating an :class:`AsyncResource`"""
    return AsyncResource(method)


class HasAsyncResources:

    _async_resource_names: Tuple[str, ...] = ()
    __slots__ = "_open", "_async_resource_state"

    def __init__(self) -> None:
        self._async_resource_state: _ResourceState = {}
        self._open = False

    def __init_subclass__(cls: Type["HasAsyncResources"]) -> None:
        for k, v in list(cls.__dict__.items()):
            if isinstance(v, AsyncResource) and k not in cls._async_resource_names:
                cls._async_resource_names += (k,)
        return None

    async def __aenter__(self: _Self) -> _Self:
        if self._open:
            raise RuntimeError(f"{self} is already open")
        self._open = True
        for rsrc_name in self._async_resource_names:
            rsrc: AsyncResource[Any] = getattr(type(self), rsrc_name)
            await rsrc.open(self)
        return self

    async def __aexit__(self, *exc: Any) -> None:
        for rsrc_name in reversed(self._async_resource_names):
            rsrc: AsyncResource[Any] = getattr(type(self), rsrc_name)
            await rsrc.close(self, *exc)
        self._open = False
        return None


class AsyncResource(Generic[_Rsrc]):

    __slots__ = "_context_manager", "_name"

    def __init__(self, method: Callable[[Any], AsyncIterator[_Rsrc]],) -> None:
        self._context_manager = asynccontextmanager(method)

    async def open(self, obj: HasAsyncResources) -> None:
        context = self._context_manager(obj)
        value = await context.__aenter__()
        obj._async_resource_state[self._name] = (context, value)
        return None

    async def close(self, obj: HasAsyncResources, *exc: Any) -> None:
        try:
            context, _ = obj._async_resource_state[self._name]
        except KeyError:
            raise RuntimeError(f"{self} is not open")

        await context.__aexit__(*exc)

        del obj._async_resource_state[self._name]

        return None

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
                return cast(_Rsrc, obj._async_resource_state[self._name][1])
            except KeyError:
                raise RuntimeError(f"Resource {self._name!r} of {obj} is not open")
