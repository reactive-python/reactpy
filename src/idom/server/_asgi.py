from __future__ import annotations

import asyncio
from typing import Any, Awaitable

from asgiref.typing import ASGIApplication
from uvicorn.config import Config as UvicornConfig
from uvicorn.server import Server as UvicornServer


async def serve_development_asgi(
    app: ASGIApplication | Any,
    host: str,
    port: int,
    started: asyncio.Event | None,
) -> None:
    """Run a development server for starlette"""
    server = UvicornServer(
        UvicornConfig(
            app,
            host=host,
            port=port,
            loop="asyncio",
            debug=True,
        )
    )

    coros: list[Awaitable[Any]] = [server.serve()]

    if started:

        async def check_if_started() -> None:
            while not server.started:
                await asyncio.sleep(0.2)
            started.set()

        coros.append(check_if_started())

    try:
        await asyncio.gather(*coros)
    finally:
        await asyncio.wait_for(server.shutdown(), timeout=3)
