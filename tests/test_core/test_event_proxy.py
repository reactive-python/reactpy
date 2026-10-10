"""Tests for the live, client backed event objects in :mod:`reactpy._event_proxy`."""

from __future__ import annotations

import asyncio
import threading
from time import monotonic
from typing import Any

import pytest

import reactpy
from reactpy._event_proxy import (
    EVENT_MARKER_KEY,
    EVENT_PROXY_REQUEST_TYPE,
    EVENT_PROXY_RESPONSE_TYPE,
    EVENT_REFERENCE_KEY,
    AsyncEvent,
    AsyncEventProxy,
    EventArguments,
    EventProxyAccessError,
    EventProxyBackend,
    EventProxyBlocked,
    EventProxyNotFound,
    EventProxyTimeout,
    EventProxyUnavailable,
    SyncEvent,
    SyncEventProxy,
    build_event_args,
    deserialize_value,
    serialize_argument,
)
from reactpy.config import (
    REACTPY_ENABLE_EVENT_PROXY,
    REACTPY_EVENT_PROXY_MAX_TIMEOUTS,
    REACTPY_EVENT_PROXY_TIMEOUT,
)
from reactpy.core.component import component
from reactpy.core.events import EventHandler, merge_event_handlers
from reactpy.core.layout import Layout
from reactpy.types import Event
from reactpy.utils import Ref
from tests.tooling.common import event_message


class Method:
    """A callable which records how it was called"""

    def __init__(self, result: Any = None) -> None:
        self.result = result
        self.calls: list[tuple[Any, ...]] = []

    def __call__(self, *args: Any) -> Any:
        self.calls.append(args)
        return self.result


class Reference:
    """Data the fake client hands over as a reference rather than inline"""

    def __init__(self, value: Any) -> None:
        self.value = value


class FakeClient:
    """Answers live event requests out of a plain Python object tree"""

    def __init__(
        self,
        backend: EventProxyBackend,
        objects: dict[str, Any],
        *,
        respond: bool = True,
        delay: float = 0.0,
    ) -> None:
        self.backend = backend
        self.objects = objects
        self.respond = respond
        self.delay = delay
        self.sent: list[dict[str, Any]] = []

    @property
    def requests(self) -> list[dict[str, Any]]:
        return [m for m in self.sent if m["type"] == EVENT_PROXY_REQUEST_TYPE]

    async def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)
        if message["type"] != EVENT_PROXY_REQUEST_TYPE or not self.respond:
            return
        asyncio.get_running_loop().call_later(self.delay, self._answer, dict(message))

    def _answer(self, message: dict[str, Any]) -> None:
        # A real client carries out the request either way - it only answers when the
        # server asked for a reply.
        should_reply = bool(message.get("reply"))
        path = list(message["path"])
        response: dict[str, Any] = {
            "type": EVENT_PROXY_RESPONSE_TYPE,
            "requestId": message["requestId"],
            "ok": True,
            "value": None,
            "error": None,
            "code": None,
        }
        root = self.objects.get(message["eventId"])
        if root is None:
            response.update(ok=False, error="not registered", code="not-found")
            if should_reply:
                self.backend.handle_response(response)
            return

        try:
            if message["call"]:
                name = path[-1] if path else ""
                parent = self._walk(root, path[:-1])
                method = parent.get(name) if isinstance(parent, dict) else None
                if not isinstance(method, Method):
                    msg = f"{name!r} is not a function"
                    raise LookupError(msg)
                value = method(*[self._read_argument(a) for a in message["args"]])
            else:
                value = self._walk(root, path)
        except LookupError as error:
            response.update(ok=False, error=str(error), code="not-found")
        else:
            response["value"] = self._serialize(value, path)
        if should_reply:
            self.backend.handle_response(response)

    def _walk(self, node: Any, path: list[str]) -> Any:
        for segment in path:
            if isinstance(node, Reference):
                node = node.value
            if isinstance(node, dict):
                if segment not in node:
                    msg = f"{segment!r} does not exist"
                    raise LookupError(msg)
                node = node[segment]
            elif isinstance(node, list):
                try:
                    node = node[int(segment)]
                except (ValueError, IndexError) as error:
                    msg = f"{segment!r} does not exist"
                    raise LookupError(msg) from error
            else:
                msg = f"cannot read {segment!r} of a {type(node).__name__}"
                raise LookupError(msg)
        return node

    def _read_argument(self, argument: Any) -> Any:
        if isinstance(argument, dict) and EVENT_REFERENCE_KEY in argument:
            reference = argument[EVENT_REFERENCE_KEY]
            return self._walk(
                self.objects[reference["eventId"]], list(reference["path"])
            )
        if isinstance(argument, list):
            return [self._read_argument(item) for item in argument]
        if isinstance(argument, dict):
            return {key: self._read_argument(item) for key, item in argument.items()}
        return argument

    def _serialize(self, value: Any, path: list[str]) -> Any:
        if isinstance(value, Method):
            return {EVENT_REFERENCE_KEY: {"path": path, "callable": True}}
        if isinstance(value, Reference):
            return {EVENT_REFERENCE_KEY: {"path": path}}
        if isinstance(value, dict):
            return {
                key: self._serialize(item, [*path, key])
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                self._serialize(item, [*path, str(index)])
                for index, item in enumerate(value)
            ]
        return value


def make_client(
    objects: dict[str, Any], *, respond: bool = True, delay: float = 0.0
) -> tuple[EventProxyBackend, FakeClient]:
    """Build a backend wired up to a fake client serving the given objects"""
    backend = EventProxyBackend()
    client = FakeClient(backend, objects, respond=respond, delay=delay)
    backend.set_sender(client.send)
    return backend, client


def requested_paths(client: FakeClient) -> list[list[str]]:
    return [request["path"] for request in client.requests]


async def poll(predicate, timeout: float = 5.0) -> None:
    """Wait until ``predicate()`` becomes truthy"""
    deadline = monotonic() + timeout
    while not predicate():
        if monotonic() > deadline:
            msg = "Timed out waiting for condition to become true"
            raise TimeoutError(msg)
        await asyncio.sleep(0.005)


def connect(layout: Layout, client: FakeClient) -> None:
    """Pipe a layout's live event requests through ``client`` and back again"""
    client.backend = layout.set_event_proxy_sender(client.send)


def make_objects() -> dict[str, Any]:
    """A stand-in for the object tree a browser would hand back"""
    return {
        "evt": {
            "type": "click",
            "target": {
                "tagName": "INPUT",
                "value": "typed",
                "focus": Method("focused"),
            },
            "deep": Reference({"a": {"b": {"c": 42}}}),
            "composedPath": Method(["window", "input"]),
            "preventDefault": Method(),
            "stopPropagation": Method(),
            "log": Method(None),
            "touches": [{"pageX": 1}, {"pageX": 2}],
        }
    }


async def test_async_event_prefers_the_snapshot():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(
        backend,
        "evt",
        snapshot={"type": "click", "target": {"value": "cached"}},
    )

    assert event_object["type"] == "click"
    assert event_object["target"]["value"] == "cached"
    assert event_object.target.value == "cached"
    assert isinstance(event_object["target"]["nope"], AsyncEventProxy)
    assert requested_paths(client) == []


async def test_async_event_resolves_what_the_snapshot_lacks():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(backend, "evt", snapshot={"type": "click"})

    assert await event_object.target.tagName == "INPUT"
    assert await event_object.read("target.value") == "typed"
    assert await event_object.read("nope", default="fallback") == "fallback"
    assert requested_paths(client) == [
        ["target", "tagName"],
        ["target", "value"],
        ["nope"],
    ]


async def test_async_event_walks_references():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(backend, "evt", snapshot={})

    deep = await event_object.deep.resolve()
    assert isinstance(deep, AsyncEventProxy)
    assert deep.path == ("deep",)
    assert await event_object.deep.a.b.c == 42
    assert await event_object.read("deep.a.b.c") == 42
    assert requested_paths(client) == [
        ["deep"],
        ["deep", "a", "b", "c"],
        ["deep", "a", "b", "c"],
    ]


async def test_async_event_calls_client_side_methods():
    objects = make_objects()
    backend, _client = make_client(objects)
    event_object = AsyncEvent(backend, "evt", snapshot={})

    assert await event_object.target.focus() == "focused"
    assert await event_object.composedPath() == ["window", "input"]
    assert objects["evt"]["target"]["focus"].calls == [()]

    await event_object.log(event_object.target, {"a": [1, 2]})
    logged_node, payload = objects["evt"]["log"].calls[-1]
    assert logged_node["tagName"] == "INPUT"
    assert logged_node["value"] == "typed"
    assert payload == {"a": [1, 2]}


async def test_prevent_default_is_scheduled_but_not_awaited():
    objects = make_objects()
    backend, client = make_client(objects)
    event_object = AsyncEvent(backend, "evt", snapshot={})

    event_object.preventDefault()
    event_object.stopPropagation()
    assert event_object.defaultPrevented
    assert event_object.propagationStopped

    await asyncio.sleep(0.01)
    assert requested_paths(client) == [["preventDefault"], ["stopPropagation"]]
    assert all(not request["reply"] for request in client.requests)
    assert objects["evt"]["preventDefault"].calls == [()]


def test_snapshot_data_is_plain_json():
    import json

    backend = EventProxyBackend()
    event_object = AsyncEvent(
        backend, "evt", snapshot={"type": "click", "target": {"value": "x"}}
    )

    assert json.loads(json.dumps(event_object)) == {
        "type": "click",
        "target": {"value": "x"},
    }
    assert list(event_object) == ["type", "target"]
    assert bool(event_object) is True
    assert event_object.debounce is None
    event_object.debounce = 120
    assert event_object.debounce == 120


async def test_sync_event_blocks_until_the_client_answers():
    objects = make_objects()
    backend, _client = make_client(objects, delay=0.01)
    event_object = SyncEvent(backend, "evt", snapshot={"type": "click"})
    outcome: Ref[tuple[Any, ...]] = Ref(None)

    def handler() -> None:
        outcome.current = (
            event_object.target.value,
            str(event_object.deep.a.b.c),
            event_object.target.focus(),
            event_object.composedPath(),
            [touch["pageX"] for touch in event_object.touches],
        )

    thread = threading.Thread(target=handler)
    thread.start()
    await asyncio.to_thread(thread.join, 10)
    assert not thread.is_alive()
    assert outcome.current == (
        "typed",
        "42",
        "focused",
        ["window", "input"],
        [1, 2],
    )


async def test_sync_access_from_the_event_loop_is_refused():
    backend, _client = make_client(make_objects())
    event_object = SyncEvent(backend, "evt", snapshot={})

    with pytest.raises(EventProxyBlocked):
        value = event_object.target.value
        assert value


async def test_unanswered_requests_eventually_disable_live_access(monkeypatch):
    monkeypatch.setattr(REACTPY_EVENT_PROXY_TIMEOUT, "current", 0.05)
    monkeypatch.setattr(REACTPY_EVENT_PROXY_MAX_TIMEOUTS, "current", 2)
    backend, _client = make_client(make_objects(), respond=False)
    event_object = AsyncEvent(backend, "evt", snapshot={})

    for _ in range(2):
        with pytest.raises(EventProxyTimeout):
            await event_object.read("target")

    assert backend.disabled
    assert not backend.available
    with pytest.raises(EventProxyUnavailable):
        await event_object.read("target")


async def test_missing_objects_and_paths_are_reported():
    backend, _client = make_client(make_objects())
    missing = AsyncEvent(backend, "not-registered", snapshot={})
    with pytest.raises(EventProxyNotFound):
        await missing.resolve()

    event_object = AsyncEvent(backend, "evt", snapshot={})
    with pytest.raises(EventProxyNotFound):
        await event_object.nope.resolve()


def test_arguments_are_serialized_or_refused():
    backend = EventProxyBackend()
    proxy = SyncEventProxy(backend, "evt", ["target"])
    assert serialize_argument(proxy) == {
        EVENT_REFERENCE_KEY: {"eventId": "evt", "path": ["target"]},
    }
    assert serialize_argument({"a": [1, "two", None]}) == {"a": [1, "two", None]}
    with pytest.raises(EventProxyAccessError):
        serialize_argument(object())


def test_excessively_nested_references_are_refused():
    backend = EventProxyBackend()
    value: Any = {EVENT_REFERENCE_KEY: {"path": ["a"]}}
    for _ in range(20):
        value = {"nested": value}

    with pytest.raises(EventProxyAccessError):
        deserialize_value(value, "evt", backend, sync=False)


def test_backend_without_a_sender_is_unavailable():
    backend = EventProxyBackend()
    assert not backend.available

    data = [{EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"}, 5]
    args, flavor = build_event_args(data, backend)
    assert isinstance(args[0], Event)
    assert args[1] == 5
    assert flavor is None


async def test_event_arguments_are_rebuilt_for_each_handler():
    backend, _client = make_client(make_objects())
    data = [{EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"}]

    arguments = EventArguments(data, backend)
    assert isinstance(arguments[0], AsyncEvent)
    assert EVENT_MARKER_KEY not in arguments[0]

    sync_arguments = arguments.rebuild(False)
    assert isinstance(sync_arguments[0], SyncEvent)
    assert arguments.rebuild(True) is arguments

    plain = EventArguments([1, "two"])
    assert plain.rebuild(False) is plain


# -- layout integration -----------------------------------------------------


def event_handlers_of(model: dict[str, Any]) -> dict[str, Any]:
    """Find the event handlers of the (single) element a test component renders"""
    if "eventHandlers" in model:
        return model["eventHandlers"]
    for child in model.get("children", []):
        if isinstance(child, dict):
            try:
                return event_handlers_of(child)
            except KeyError:
                continue
    msg = "no event handlers in model"
    raise KeyError(msg)


async def test_layout_hands_handlers_events_of_their_own_flavour(monkeypatch):
    monkeypatch.setattr(REACTPY_ENABLE_EVENT_PROXY, "current", True)
    main_thread = threading.current_thread().name
    received: dict[str, tuple[Any, str, Any]] = {}
    objects = make_objects()

    async def async_handler(event_object):
        received["async"] = (
            event_object,
            threading.current_thread().name,
            await event_object.read("target.value"),
        )

    def sync_handler(event_object):
        received["sync"] = (
            event_object,
            threading.current_thread().name,
            event_object.target.value,
        )

    @component
    def MyComponent():
        return reactpy.html.div(
            {"onSync": sync_handler, "onAsync": async_handler}
        )

    _backend, client = make_client(objects)

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handlers = event_handlers_of(model)
        assert all(handler["eventProxy"] for handler in handlers.values())

        data = {EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"}
        await layout.deliver(event_message(handlers["onSync"]["target"], dict(data)))
        await poll(lambda: "sync" in received)
        await layout.deliver(event_message(handlers["onAsync"]["target"], dict(data)))
        await poll(lambda: "async" in received)

    sync_event, sync_thread, sync_value = received["sync"]
    assert isinstance(sync_event, SyncEvent)
    assert sync_value == "typed"
    assert sync_thread != main_thread, "blocking handlers run off the event loop"

    async_event, async_thread, async_value = received["async"]
    assert isinstance(async_event, AsyncEvent)
    assert async_value == "typed"
    assert async_thread == main_thread

    assert requested_paths(client) == [["target"], ["target", "value"]]


async def test_layout_respects_the_per_handler_kill_switch():
    received: dict[str, Any] = {}

    def sync_handler(args):
        received["event"] = args[0]

    @component
    def MyComponent():
        return reactpy.html.div(
            {"onClick": EventHandler(sync_handler, event_proxy=False)}
        )

    _backend, client = make_client(make_objects())

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handlers = event_handlers_of(model)
        assert "eventProxy" not in handlers["onClick"]

        target = handlers["onClick"]["target"]
        await layout.deliver(
            event_message(target, {EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"})
        )
        await poll(lambda: "event" in received)

    assert type(received["event"]) is Event
    assert received["event"]["type"] == "click"
    assert client.requests == []


async def test_merged_handlers_get_the_flavour_each_needs(monkeypatch):
    monkeypatch.setattr(REACTPY_ENABLE_EVENT_PROXY, "current", True)
    received: dict[str, Any] = {}

    def sync_handler(args):
        received["sync"] = args[0]

    async def async_handler(args):
        received["async"] = args[0]

    merged = merge_event_handlers(
        [EventHandler(sync_handler), EventHandler(async_handler)]
    )

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": merged})

    _backend, client = make_client(make_objects())

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        target = event_handlers_of(model)["onClick"]["target"]
        await layout.deliver(
            event_message(target, {EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"})
        )
        await poll(lambda: len(received) == 2)

    assert isinstance(received["sync"], SyncEvent)
    assert isinstance(received["async"], AsyncEvent)


async def test_layout_without_a_client_falls_back_to_snapshots():
    received: dict[str, Any] = {}

    def sync_handler(event):
        received["event"] = event

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": sync_handler})

    async with Layout(MyComponent()) as layout:
        model = (await layout.render())["model"]
        target = event_handlers_of(model)["onClick"]["target"]
        await layout.deliver(
            event_message(target, {EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"})
        )
        await poll(lambda: "event" in received)

    # nobody bound a sender, so the live marker is simply dropped
    assert type(received["event"]) is Event
    assert EVENT_MARKER_KEY not in received["event"]


async def test_proxy_responses_are_routed_not_delivered():
    _backend, client = make_client(make_objects())

    @component
    def MyComponent():
        return reactpy.html.div()

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        assert layout.handle_event_proxy_response(
            {"type": EVENT_PROXY_RESPONSE_TYPE, "requestId": "unknown", "ok": True}
        )
        assert not layout.handle_event_proxy_response({"type": "layout-update"})


async def test_stop_immediate_propagation_is_detected_and_forwarded():
    def on_click(event):
        event.stopImmediatePropagation()

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": on_click})

    async with Layout(MyComponent()) as layout:
        model = (await layout.render())["model"]
        handler = event_handlers_of(model)["onClick"]
        assert handler["stopPropagation"] is True
        assert handler["stopImmediatePropagation"] is True

