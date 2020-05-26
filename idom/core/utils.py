import inspect
from functools import wraps
from types import TracebackType
from typing import TypeVar, Any, Type, Callable, Optional


_Self = TypeVar("_Self")
_Func = TypeVar("_Func")


def must_by_open(
    if_closed: Type[Exception] = RuntimeError,
    if_not_open: Type[Exception] = RuntimeError,
) -> Callable[[_Func], _Func]:
    def setup(method: _Func) -> _Func:
        if inspect.iscoroutinefunction(method):

            @wraps(method)
            async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
                if self.closed:
                    raise if_closed(f"{self} is closed")
                elif not self.opened:
                    raise if_not_open(f"{self} is not open")
                return await method(self, *args, **kwargs)

        else:

            @wraps(method)
            def wrapper(self, *args: Any, **kwargs: Any) -> Any:
                if self.closed:
                    raise if_closed(f"{self} is closed")
                elif not self.opened:
                    raise if_not_open(f"{self} is not open")
                return method(self, *args, **kwargs)

        return wrapper

    return setup


class AsyncOpenClose:

    __slots__ = "_opened", "_closed"

    def __init__(self):
        self._opened = self._closed = False

    @property
    def opened(self) -> bool:
        return self._opened

    @property
    def closed(self) -> bool:
        return self._closed

    async def open(self) -> None:
        if self._closed:
            raise RuntimeError(f"{self} is closed")
        self._opened = True

    async def close(self) -> None:
        self._opened = False
        self._closed = True

    async def __aenter__(self: _Self) -> _Self:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()
        return None
