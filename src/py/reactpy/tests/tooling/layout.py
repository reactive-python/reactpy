from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from jsonpointer import set_pointer

from reactpy.core.layout import Layout
from reactpy.core.types import VdomJson
from tests.tooling.common import event_message

logger = logging.getLogger(__name__)


@asynccontextmanager
async def layout_runner(layout: Layout) -> AsyncIterator[LayoutRunner]:
    async with layout:
        yield LayoutRunner(layout)


class LayoutRunner:
    def __init__(self, layout: Layout) -> None:
        self.layout = layout
        self.model = {}

    async def render(self) -> VdomJson:
        update = await self.layout.render()
        logger.info(f"Rendering element at {update['path'] or '/'!r}")
        if not update["path"]:
            self.model = update["model"]
        else:
            self.model = set_pointer(
                self.model, update["path"], update["model"], inplace=False
            )
        return self.model

    async def trigger(self, element: VdomJson, event_name: str, *data: Any) -> None:
        event_handler = element.get("eventHandlers", {}).get(event_name, {})
        logger.info(f"Triggering {event_name!r} with target {event_handler['target']}")
        if not event_handler:
            raise ValueError(f"Element has no event handler for {event_name}")
        await self.layout.deliver(event_message(event_handler["target"], *data))
