"""These types are separated from the main module to avoid dependency issues."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any, Protocol

from asgiref import typing as asgi_types

# Type hints for `receive` within `asgi_app(scope, receive, send)`
AsgiReceive = Callable[[], Awaitable[dict[str, Any] | MutableMapping[str, Any]]]
AsgiHttpReceive = (
    Callable[
        [], Awaitable[asgi_types.HTTPRequestEvent | asgi_types.HTTPDisconnectEvent]
    ]
    | AsgiReceive
)
AsgiWebsocketReceive = (
    Callable[
        [],
        Awaitable[
            asgi_types.WebSocketConnectEvent
            | asgi_types.WebSocketDisconnectEvent
            | asgi_types.WebSocketReceiveEvent
        ],
    ]
    | AsgiReceive
)
AsgiLifespanReceive = (
    Callable[
        [],
        Awaitable[asgi_types.LifespanStartupEvent | asgi_types.LifespanShutdownEvent],
    ]
    | AsgiReceive
)

# Type hints for `send` within `asgi_app(scope, receive, send)`
AsgiSend = Callable[[dict[str, Any] | MutableMapping[str, Any]], Awaitable[None]]
AsgiHttpSend = (
    Callable[
        [
            asgi_types.HTTPResponseStartEvent
            | asgi_types.HTTPResponseBodyEvent
            | asgi_types.HTTPResponseTrailersEvent
            | asgi_types.HTTPServerPushEvent
            | asgi_types.HTTPDisconnectEvent
        ],
        Awaitable[None],
    ]
    | AsgiSend
)
AsgiWebsocketSend = (
    Callable[
        [
            asgi_types.WebSocketAcceptEvent
            | asgi_types.WebSocketSendEvent
            | asgi_types.WebSocketResponseStartEvent
            | asgi_types.WebSocketResponseBodyEvent
            | asgi_types.WebSocketCloseEvent
        ],
        Awaitable[None],
    ]
    | AsgiSend
)
AsgiLifespanSend = (
    Callable[
        [
            asgi_types.LifespanStartupCompleteEvent
            | asgi_types.LifespanStartupFailedEvent
            | asgi_types.LifespanShutdownCompleteEvent
            | asgi_types.LifespanShutdownFailedEvent
        ],
        Awaitable[None],
    ]
    | AsgiSend
)

# Type hints for `scope` within `asgi_app(scope, receive, send)`
AsgiScope = dict[str, Any] | MutableMapping[str, Any]
AsgiHttpScope = asgi_types.HTTPScope | AsgiScope
AsgiWebsocketScope = asgi_types.WebSocketScope | AsgiScope
AsgiLifespanScope = asgi_types.LifespanScope | AsgiScope


# Type hints for the ASGI app interface
AsgiV3App = Callable[[AsgiScope, AsgiReceive, AsgiSend], Awaitable[None]]
AsgiV3HttpApp = Callable[
    [AsgiHttpScope, AsgiHttpReceive, AsgiHttpSend], Awaitable[None]
]
AsgiV3WebsocketApp = Callable[
    [AsgiWebsocketScope, AsgiWebsocketReceive, AsgiWebsocketSend], Awaitable[None]
]
AsgiV3LifespanApp = Callable[
    [AsgiLifespanScope, AsgiLifespanReceive, AsgiLifespanSend], Awaitable[None]
]


class AsgiV2Protocol(Protocol):
    """The ASGI 2.0 protocol for ASGI applications. Type hints for parameters are not provided since
    type checkers tend to be too strict with protocol method types matching up perfectly."""

    def __init__(self, scope: Any) -> None: ...

    async def __call__(self, receive: Any, send: Any) -> None: ...


AsgiV2App = type[AsgiV2Protocol]
AsgiApp = AsgiV3App | AsgiV2App
"""The type hint for any ASGI application. This was written to be as generic as possible to avoid type checking issues."""
