from weakref import ref
from typing import Callable, Awaitable, Any, Optional, Dict, Generic, TypeVar, cast

from idom.core.events import Events
from idom.core.element import AbstractElement
from idom.core.vdom import VdomDict

from .html import html


_Callback = Callable[["Input", str], Awaitable[None]]
_InputType = TypeVar("_InputType")

_pass_through = cast(Callable[[str], _InputType], lambda x: x)


class Input(Generic[_InputType], AbstractElement):
    """An input element.

    Parameters:
        type:
            the kind of input element
        value:
            an initial value
        attributes:
            Attributes passed into the ``<input/>``.
        label:
            A label for the input. If the ``<input/>`` is wrapped inside a
            ``<label/>`` element.
        ignore_empty:
            Whether or not to ignore updates where the value is ``''``.

    """

    __slots__ = (
        "_type",
        "_value",
        "_cast",
        "_display_value",
        "_ignore_empty",
        "_events",
        "_attributes",
    )

    def __init__(
        self,
        type: str,
        value: _InputType = "",  # type: ignore
        attributes: Optional[Dict[str, Any]] = None,
        cast: Callable[[str], _InputType] = _pass_through,
        ignore_empty: bool = True,
    ) -> None:
        super().__init__()
        self._type = type
        self._value = value
        self._display_value = str(value)
        self._cast = cast
        self._ignore_empty = ignore_empty
        self._events = Events()
        self._attributes = attributes or {}
        self_ref = ref(self)

        @self._events.on("change")
        async def on_change(event: Dict[str, Any]) -> None:
            self_deref = self_ref()
            if self_deref is not None:
                self_deref._set_str_value(event["value"])

    @property
    def value(self) -> _InputType:
        """The current value of the input."""
        return self._value

    @property
    def events(self) -> Events:
        """Events associated with the ``<input/>``"""
        return self._events

    @property
    def attributes(self) -> Dict[str, Any]:
        return self._attributes

    def update(self, value: _InputType) -> None:
        """Update the current value of the input."""
        self._set_value(value)

    async def render(self) -> VdomDict:
        input_element = html.input(
            self.attributes,
            {"type": self._type, "value": self._display_value},
            event_handlers=self.events,
        )
        return input_element

    def _set_str_value(self, value: str) -> None:
        self._display_value = value
        super().update()
        print(value)
        if not value and self._ignore_empty:
            return
        self._value = self._cast(value)

    def _set_value(self, value: _InputType) -> None:
        self._display_value = str(value)
        self._value = value
        super().update()

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}({self.value!r})"
