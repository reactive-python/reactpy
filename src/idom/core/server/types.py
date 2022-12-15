from __future__ import annotations

from typing import Any, Callable, TypedDict, TypeVar, Union, get_type_hints

from typing_extensions import Literal, Protocol, TypeGuard

from idom.core.layout import LayoutEvent, LayoutUpdate


class FileHandler(Protocol):
    async def handle(self, message: FileUploadMessage) -> None:
        ...


_Type = TypeVar("_Type")


def _make_message_type_guard(
    msg_type: type[_Type],
) -> Callable[[Any], TypeGuard[_Type]]:
    annotations = get_type_hints(msg_type)
    type_anno_args = getattr(annotations["type"], "__args__")
    assert (
        isinstance(type_anno_args, tuple)
        and len(type_anno_args) == 1
        and isinstance(type_anno_args[0], str)
    )
    expected_type = type_anno_args[0]

    def type_guard(value: _Type) -> TypeGuard[_Type]:
        assert isinstance(value, dict)
        return value["type"] == expected_type

    type_guard.__doc__ = f"Check wheter the given value is a {expected_type!r} message"

    return type_guard


ServerMessage = "ServerInfoMessage"

ClientMessage = Union[
    "ClientInfoMessage",
    "LayoutEventMessage",
    "FileUploadMessage",
]

ServerInfoMessage = TypedDict(
    "ServerInfoMessage",
    {
        "type": Literal["server-info"],
        "version": str,
    },
)
is_server_info_message = _make_message_type_guard(ServerInfoMessage)

ClientInfoMessage = TypedDict(
    "ClientInfoMessage",
    {
        "type": Literal["client-info"],
        "version": str,
    },
)
is_client_info_message = _make_message_type_guard(ClientInfoMessage)


LayoutUpdateMessage = TypedDict(
    "LayoutUpdateMessage",
    {
        "type": Literal["layout-update"],
        "data": LayoutUpdate,
    },
)
is_layout_udpate_message = _make_message_type_guard(LayoutUpdateMessage)

LayoutEventMessage = TypedDict(
    "LayoutEventMessage",
    {
        "type": Literal["layout-event"],
        "data": LayoutEvent,
    },
)
is_layout_event_message = _make_message_type_guard(LayoutEventMessage)

FileUploadMessage = TypedDict(
    "FileUploadMessage",
    {
        "type": Literal["file-upload"],
        "file": str,
        "data": bytes,
        "bytes-chunk-size": int,
        "bytes-sent": int,
        "bytes-remaining": int,
    },
)
is_file_upload_message = _make_message_type_guard(FileUploadMessage)
