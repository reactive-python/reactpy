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
        "_value",
        "_cast",
        "_display_value",
        "_label",
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
        label: Optional[str] = None,
        ignore_empty: bool = True,
    ) -> None:
        super().__init__()
        self._value = value
        self._display_value = str(value)
        self._cast = cast
        self._label = label
        self._ignore_empty = ignore_empty
        self._events = Events()
        self._attributes = attributes or {}
        self._attributes["type"] = type
        self_ref = ref(self)

        @self._events.on("change")
        async def on_change(event: Dict[str, Any]) -> None:
            self_deref = self_ref()
            if self_deref is not None:
                value = self_deref._cast(event["value"])
                self_deref.update(value)

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
        super().update()

    async def render(self) -> VdomDict:
        input_element = html.input(
            self.attributes, {"value": self._display_value}, event_handlers=self.events,
        )
        if self._label is not None:
            return html.label([self._label, input_element])
        else:
            return input_element

    def _set_value(self, value: _InputType) -> None:
        self._display_value = str(value)
        if self._ignore_empty and not value:
            return
        self._value = value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"
