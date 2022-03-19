from __future__ import annotations

import asyncio
from typing import Any

from idom.types import RootComponentConstructor

from .utils import default_implementation


def configure(app: Any, component: RootComponentConstructor) -> None:
    """Configure the given app instance to display the given component"""
    return default_implementation().configure(app, component)


def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return default_implementation().create_development_app()


async def serve_development_app(
    app: Any, host: str, port: int, started: asyncio.Event
) -> None:
    """Run an application using a development server"""
    return await default_implementation().serve_development_app(
        app, host, port, started
    )
