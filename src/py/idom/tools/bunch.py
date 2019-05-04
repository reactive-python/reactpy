from typing import Mapping, MutableMapping

from typing import Iterator, Any


class StaticBunch(Mapping[str, Any]):
    """An immutable mapping with attribute access."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__dict__.update(*args, **kwargs)

    def __contains__(self, name: Any) -> bool:
        return name in self.__dict__

    def __len__(self) -> int:
        return len(self.__dict__)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)

    def __getitem__(self, name: str) -> Any:
        return self.__dict__[name]

    def __repr__(self) -> str:
        return repr(self.__dict__)

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypeError("%r is immutable." % type(self).__name__)

    def __delattr__(self, name: str) -> None:
        raise TypeError("%r is immutable." % type(self).__name__)


class DynamicBunch(MutableMapping[str, Any], StaticBunch):
    """A mutable mapping with attribute access."""

    def __setitem__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __delitem__(self, name: str) -> None:
        del self.__dict__[name]

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        del self[name]
