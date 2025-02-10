"""These types are separated from the main module to avoid dependency issues."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Callable, Union

from asgiref import typing as asgi_types

AsgiHttpReceive = Callable[
    [],
    Awaitable[asgi_types.HTTPRequestEvent | asgi_types.HTTPDisconnectEvent],
]

AsgiHttpSend = Callable[
    [
        asgi_types.HTTPResponseStartEvent
        | asgi_types.HTTPResponseBodyEvent
        | asgi_types.HTTPResponseTrailersEvent
        | asgi_types.HTTPServerPushEvent
        | asgi_types.HTTPDisconnectEvent
    ],
    Awaitable[None],
]

AsgiWebsocketReceive = Callable[
    [],
    Awaitable[
        asgi_types.WebSocketConnectEvent
        | asgi_types.WebSocketDisconnectEvent
        | asgi_types.WebSocketReceiveEvent
    ],
]

AsgiWebsocketSend = Callable[
    [
        asgi_types.WebSocketAcceptEvent
        | asgi_types.WebSocketSendEvent
        | asgi_types.WebSocketResponseStartEvent
        | asgi_types.WebSocketResponseBodyEvent
        | asgi_types.WebSocketCloseEvent
    ],
    Awaitable[None],
]

AsgiLifespanReceive = Callable[
    [],
    Awaitable[asgi_types.LifespanStartupEvent | asgi_types.LifespanShutdownEvent],
]

AsgiLifespanSend = Callable[
    [
        asgi_types.LifespanStartupCompleteEvent
        | asgi_types.LifespanStartupFailedEvent
        | asgi_types.LifespanShutdownCompleteEvent
        | asgi_types.LifespanShutdownFailedEvent
    ],
    Awaitable[None],
]

AsgiHttpApp = Callable[
    [asgi_types.HTTPScope, AsgiHttpReceive, AsgiHttpSend],
    Awaitable[None],
]

AsgiWebsocketApp = Callable[
    [asgi_types.WebSocketScope, AsgiWebsocketReceive, AsgiWebsocketSend],
    Awaitable[None],
]

AsgiLifespanApp = Callable[
    [asgi_types.LifespanScope, AsgiLifespanReceive, AsgiLifespanSend],
    Awaitable[None],
]


AsgiApp = Union[AsgiHttpApp, AsgiWebsocketApp, AsgiLifespanApp]
