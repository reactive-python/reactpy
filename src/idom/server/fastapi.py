from __future__ import annotations

from fastapi import FastAPI

from . import starlette


serve_development_app = starlette.serve_development_app
"""Alias for :func:`idom.server.starlette.serve_development_app`"""

# see: https://github.com/idom-team/flake8-idom-hooks/issues/12
use_scope = starlette.use_scope  # noqa: ROH101
"""Alias for :func:`idom.server.starlette.use_scope`"""

# see: https://github.com/idom-team/flake8-idom-hooks/issues/12
use_websocket = starlette.use_websocket  # noqa: ROH101
"""Alias for :func:`idom.server.starlette.use_websocket`"""

Options = starlette.Options
"""Alias for :class:`idom.server.starlette.Options`"""

configure = starlette.configure
"""Alias for :class:`idom.server.starlette.configure`"""


def create_development_app() -> FastAPI:
    """Create a development ``FastAPI`` application instance."""
    return FastAPI(debug=True)
