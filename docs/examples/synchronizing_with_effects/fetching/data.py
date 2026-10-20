"""A slow data source, slow on purpose so two requests can overlap."""

import asyncio

# Deliberately asymmetric: `orders` is slow and `users` is fast, so a
# switch made while `orders` is in flight proves that the stale answer
# never lands.
LATENCIES = {"orders": 0.8, "users": 0.05}


class Catalog:
    def __init__(self):
        self.answers = []

    async def fetch(self, name):
        await asyncio.sleep(LATENCIES.get(name, 0.2))
        answer = f"{name}: {len(name) * 100} rows"
        self.answers.append(answer)
        return answer


catalog = Catalog()
