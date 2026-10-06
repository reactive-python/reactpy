# start

import asyncio
import json

import websockets


async def main():
    url = "ws://127.0.0.1:8000/reactpy/main.counter/?path=%2F"

    async with websockets.connect(url) as socket:
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
                    "data": [{"type": "click", "target": {"tagName": "BUTTON"}}],
                    "seq": 1,
                }
            )
        )

        patch = json.loads(await socket.recv())
        print("\n3. the reply is a patch at path:", repr(patch["path"]))
        print(json.dumps(patch["model"], indent=2))


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
