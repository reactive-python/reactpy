from __future__ import annotations

import asyncio
from asyncio import FIRST_EXCEPTION, CancelledError

from asgiref.typing import ASGIApplication
from uvicorn.config import Config as UvicornConfig
from uvicorn.server import Server as UvicornServer


async def serve_development_asgi(
    app: ASGIApplication,
    host: str,
    port: int,
    started: asyncio.Event,
) -> None:
    """Run a development server for starlette"""
    server = UvicornServer(UvicornConfig(app, host=host, port=port, loop="asyncio"))

    async def check_if_started():
        while not server.started:
            await asyncio.sleep(0.2)
        started.set()

    try:
        await asyncio.gather(server.serve(), check_if_started())
    finally:
        await asyncio.wait_for(server.shutdown(), timeout=3)
