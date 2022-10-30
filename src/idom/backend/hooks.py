from __future__ import annotations

from typing import Any, MutableMapping

from idom.core.hooks import Context, create_context, use_context

from .types import Connection, Location


# backend implementations should establish this context at the root of an app
ConnectionContext: Context[Connection[Any] | None] = create_context(None)


def use_connection() -> Connection[Any]:
    conn = use_context(ConnectionContext)
    if conn is None:
        raise RuntimeError("No backend established a connection.")  # pragma: no cover
    return conn


def use_scope() -> MutableMapping[str, Any]:
    return use_connection().scope


def use_location() -> Location:
    return use_connection().location
