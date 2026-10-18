# start

import asyncio
import json

import websockets

URL = "ws://127.0.0.1:8000/reactpy/main.counter/?path=%2F"


async def main():
    patches = asyncio.Queue()

    async with websockets.connect(URL) as socket:
        mount = json.loads(await socket.recv())
        print("1. the mount update:", mount["path"] or "(root)")
        print(json.dumps(mount["model"], indent=2))

        target = find_handler_target(mount["model"])
        print("\n2. sending a click to", target)
        await socket.send(
            json.dumps(
                {
                    "type": "layout-event",
                    "target": target,
                    # The client keeps the DOM event and sends a handle, not a copy
                    # of it. "type" is the one plain value sent along up front.
                    "data": [
                        {"__reactpy_event__": {"id": "lzk4q1-0"}, "type": "click"}
                    ],
                    "seq": 1,
                }
            )
        )

        # One reader for the whole connection: answer proxy requests as they arrive
        # and hand everything else to the caller. Two consumers on one websocket
        # would race for each frame. With a handler which only calls a state setter
        # — the counter this observes — no proxy request is ever sent, and this task
        # simply forwards patches.
        reading = asyncio.create_task(read(socket, patches))
        try:
            patch = await asyncio.wait_for(patches.get(), timeout=10)
            print("\n3. the reply is a patch at path:", repr(patch["path"]))
            print(json.dumps(patch["model"], indent=2))
        finally:
            reading.cancel()


async def read(socket, patches):
    async for raw in socket:
        message = json.loads(raw)
        if message.get("type") == "event-proxy-request":
            await answer_requests(socket, message)
        else:
            await patches.put(message)


async def answer_requests(socket, message):
    """Reply to every property path the server is asking about"""
    requests = message.get("requests", [message])
    for request in requests:
        print("   the server asks for", request["path"])
    if "requests" in message:
        await socket.send(
            json.dumps(
                {
                    "type": "event-proxy-response",
                    "responses": [answer(request) for request in requests],
                }
            )
        )
    else:
        await socket.send(json.dumps(answer(requests[0])))


def answer(request):
    """The value behind one property path, in the shape the client must use"""
    return {
        "type": "event-proxy-response",
        "requestId": request["requestId"],
        "ok": True,
        "value": "typed text" if request["path"][-1] == "value" else None,
        "error": None,
        "code": None,
    }


def find_handler_target(model):
    """Return the target of the first event handler found in a model."""
    if isinstance(model, dict):
        for spec in (model.get("eventHandlers") or {}).values():
            return spec["target"]
        for child in model.get("children", []):
            found = find_handler_target(child)
            if found:
                return found
    return None


asyncio.run(main())
