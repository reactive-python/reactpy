from __future__ import annotations

from fastapi import FastAPI

from . import starlette


serve_development_app = starlette.serve_development_app
"""Alias for :func:`idom.backend.starlette.serve_development_app`"""

# see: https://github.com/idom-team/flake8-idom-hooks/issues/12
use_location = starlette.use_location  # noqa: ROH101
"""Alias for :func:`idom.backend.starlette.use_location`"""

# see: https://github.com/idom-team/flake8-idom-hooks/issues/12
use_scope = starlette.use_scope  # noqa: ROH101
"""Alias for :func:`idom.backend.starlette.use_scope`"""

# see: https://github.com/idom-team/flake8-idom-hooks/issues/12
use_websocket = starlette.use_websocket  # noqa: ROH101
"""Alias for :func:`idom.backend.starlette.use_websocket`"""

Options = starlette.Options
"""Alias for :class:`idom.backend.starlette.Options`"""

configure = starlette.configure
"""Alias for :class:`idom.backend.starlette.configure`"""


def create_development_app() -> FastAPI:
    """Create a development ``FastAPI`` application instance."""
    return FastAPI(debug=True)
