from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Callable

from reactpy.backend.types import Connection, Location
from reactpy.core.hooks import (
    ReconnectingOnly,
    _EffectApplyFunc,
    create_context,
    use_context,
    use_effect,
)
from reactpy.core.types import Context

# backend implementations should establish this context at the root of an app
ConnectionContext: Context[Connection[Any] | None] = create_context(None)


def use_connection() -> Connection[Any]:
    """Get the current :class:`~reactpy.backend.types.Connection`."""
    conn = use_context(ConnectionContext)
    if conn is None:  # nocov
        msg = "No backend established a connection."
        raise RuntimeError(msg)
    return conn


def use_scope() -> MutableMapping[str, Any]:
    """Get the current :class:`~reactpy.backend.types.Connection`'s scope."""
    return use_connection().scope


def use_location() -> Location:
    """Get the current :class:`~reactpy.backend.types.Connection`'s location."""
    return use_connection().location


def use_reconnect_effect(
    function: _EffectApplyFunc | None = None,
) -> Callable[[_EffectApplyFunc], None] | None:
    """Apply an effect only on reconnection"""
    return use_effect(function, ReconnectingOnly())
