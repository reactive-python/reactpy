import os
from collections.abc import Mapping

STATIC = os.path.join(os.path.dirname(__file__), "static")


class Bunch(Mapping):
    """An immutable mapping with attribute access."""

    __slots__ = "_data_"

    def __init__(self, data):
        object.__setattr__(self, "_data_", data)

    def __len__(self):
        return len(self._data_)

    def __iter__(self):
        return iter(self._data_)

    def __getitem__(self, name):
        return self._data_[name]

    def __getattr__(self, name):
        return self._data_[name]
