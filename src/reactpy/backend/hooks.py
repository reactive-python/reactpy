from __future__ import annotations  # nocov

from collections.abc import MutableMapping  # nocov
from typing import Any  # nocov

from reactpy._warnings import warn  # nocov
from reactpy.backend.types import Connection, Location  # nocov
from reactpy.core.hooks import ConnectionContext, use_context  # nocov


def use_connection() -> Connection[Any]:  # nocov
    """Get the current :class:`~reactpy.backend.types.Connection`."""
    warn(
        "The module reactpy.backend.hooks has been deprecated and will be deleted in the future. "
        "Call reactpy.use_connection instead.",
        DeprecationWarning,
    )

    conn = use_context(ConnectionContext)
    if conn is None:
        msg = "No backend established a connection."
        raise RuntimeError(msg)
    return conn


def use_scope() -> MutableMapping[str, Any]:  # nocov
    """Get the current :class:`~reactpy.backend.types.Connection`'s scope."""
    warn(
        "The module reactpy.backend.hooks has been deprecated and will be deleted in the future. "
        "Call reactpy.use_scope instead.",
        DeprecationWarning,
    )

    return use_connection().scope


def use_location() -> Location:  # nocov
    """Get the current :class:`~reactpy.backend.types.Connection`'s location."""
    warn(
        "The module reactpy.backend.hooks has been deprecated and will be deleted in the future. "
        "Call reactpy.use_location instead.",
        DeprecationWarning,
    )

    return use_connection().location
