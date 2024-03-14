from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from reactpy._warnings import warn
from reactpy.backend.types import Connection, Location
from reactpy.core.hooks import ConnectionContext, use_context


def use_connection() -> Connection[Any]:
    """Get the current :class:`~reactpy.backend.types.Connection`."""
    warn(
        "The module reactpy.backend.hooks has been deprecated and will be deleted in the future. ",
        "Call use_connection in reactpy.core.hooks instead.",
        DeprecationWarning,
    )

    conn = use_context(ConnectionContext)
    if conn is None:  # nocov
        msg = "No backend established a connection."
        raise RuntimeError(msg)
    return conn


def use_scope() -> MutableMapping[str, Any]:
    """Get the current :class:`~reactpy.backend.types.Connection`'s scope."""
    warn(
        "The module reactpy.backend.hooks has been deprecated and will be deleted in the future. ",
        "Call use_scope in reactpy.core.hooks instead.",
        DeprecationWarning,
    )

    return use_connection().scope


def use_location() -> Location:
    """Get the current :class:`~reactpy.backend.types.Connection`'s location."""
    warn(
        "The module reactpy.backend.hooks has been deprecated and will be deleted in the future. ",
        "Call use_location in reactpy.core.hooks instead.",
        DeprecationWarning,
    )

    return use_connection().location
