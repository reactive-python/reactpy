from __future__ import annotations

from typing import Any

from idom.core.hooks import create_context
from idom.types import Context


Connection: type[Context[Any | None]] = create_context(None, name="Connection")
