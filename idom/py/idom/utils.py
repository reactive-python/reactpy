import os
from collections.abc import Mapping

from typing import Iterator, Tuple, Any

STATIC = os.path.join(os.path.dirname(__file__), "static")


class Bunch(Mapping):
    """An immutable mapping with attribute access."""

    __slots__ = "_data_"

    def __init__(self, data):
        object.__setattr__(self, "_data_", data)

    def __len__(self) -> int:
        return len(self._data_)

    def __iter__(self) -> Iterator[Tuple[Any, Any]]:
        return iter(self._data_)

    def __getitem__(self, name: Any) -> Any:
        return self._data_[name]

    def __getattr__(self, name: Any) -> Any:
        return self._data_[name]

    def __repr__(self):
        items = ", ".join("%s=%r" % i for i in self._data_.items())
        return "%s(%s)" % (type(self).__name__, items)
