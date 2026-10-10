"""A report source that returns rows, so the shape can be built in render."""

import asyncio

REPORTS = {
    "orders": {"pending": 12, "shipped": 40, "returned": 3},
    "users": {"active": 87, "invited": 9, "blocked": 1},
}


class Catalog:
    def __init__(self):
        self.requests = []

    async def fetch(self, name):
        self.requests.append(name)
        await asyncio.sleep(0.05)
        return REPORTS[name]


catalog = Catalog()
