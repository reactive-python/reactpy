from typing import Callable, Awaitable, Any, Optional, Dict

from idom.core import Events, AbstractElement

from . import html


_Callback = Callable[["Input", str], Awaitable[None]]


class Input(AbstractElement):
    """An input element.

    Parameters:
        type:
            the kind of input element
        value:
            an initial value
        label:
            A label for the input. If given the ``<input/>`` in is wrapped inside a
            ``<label/>`` element.
        ignore_empty:
            Whether or not to ignore updates where the value is ``''``.
        attributes:
            Attributes passed into the ``<input/>``.
    """

    __slots__ = (
        "_type",
        "_value",
        "_display_value",
        "_label",
        "_ignore_empty",
        "_events",
        "_attributes",
    )

    def __init__(
        self,
        type: str,
        value: Any = "",
        label: Optional[str] = None,
        ignore_empty: bool = True,
        **attributes: Any,
    ) -> None:
        super().__init__()
        self._type = type
        self._value = self._display_value = str(value)
        self._label = label
        self._ignore_empty = ignore_empty
        self._events = Events(bound=self)
        self._attributes = attributes

        @self._events.on("change", using="value=target.value")
        async def on_change(self: "Input", value: str) -> None:
            self.update(value)

    @property
    def value(self) -> str:
        """The current value of the input."""
        return self._value

    @property
    def events(self) -> Events:
        """Events associated with the ``<input/>``"""
        return self._events

    def update(self, value: Any) -> None:
        """Update the current value of the input."""
        value = str(value)
        self._set_value(value)
        self._update_layout()

    async def render(self) -> Dict[str, Any]:
        if self._label is not None:
            return html.label(
                self._label,
                html.input(
                    type=self._type,
                    value=self._display_value,
                    eventHandlers=self._events,
                    **self._attributes,
                ),
            )
        else:
            return html.input(
                type=self._type,
                value=self._display_value,
                eventHandlers=self._events,
                **self._attributes,
            )

    def _set_value(self, value: str) -> None:
        self._display_value = value
        if self._ignore_empty and value == "":
            return
        self._value = value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self._type)}, {self.value})"
