"""Records what the form actually sent, so the page can count submissions."""

import asyncio

sent = []


async def send_email(address):
    """Stands in for an HTTP call. Appends to `sent` when it actually runs."""
    await asyncio.sleep(0)
    sent.append(address)
    return True
