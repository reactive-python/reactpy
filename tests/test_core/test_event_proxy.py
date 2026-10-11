"""Tests for the live, client backed event objects in :mod:`reactpy._event_proxy`."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from time import monotonic
from types import MappingProxyType
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
    EventProxy,
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
    REACTPY_EVENT_PROXY_MAX_TIMEOUTS,
    REACTPY_EVENT_PROXY_TIMEOUT,
)
from reactpy.core.component import component
from reactpy.core.events import EventHandler, event, merge_event_handlers
from reactpy.core.layout import Layout
from reactpy.testing import assert_reactpy_did_log
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
                key: self._serialize(item, [*path, key]) for key, item in value.items()
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


class CannedClient:
    """Answers every live request with one fixed response payload"""

    def __init__(
        self,
        backend: EventProxyBackend,
        *,
        ok: bool,
        value: Any = None,
        error: str | None = None,
        code: str | None = None,
    ) -> None:
        self.backend = backend
        self.ok = ok
        self.value = value
        self.error = error
        self.code = code
        self.sent: list[dict[str, Any]] = []

    @property
    def requests(self) -> list[dict[str, Any]]:
        return [m for m in self.sent if m["type"] == EVENT_PROXY_REQUEST_TYPE]

    async def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)
        if message["type"] != EVENT_PROXY_REQUEST_TYPE or not message.get("reply"):
            return
        self.backend.handle_response(
            {
                "type": EVENT_PROXY_RESPONSE_TYPE,
                "requestId": message["requestId"],
                "ok": self.ok,
                "value": self.value,
                "error": self.error,
                "code": self.code,
            }
        )


def make_canned_client(**response: Any) -> tuple[EventProxyBackend, CannedClient]:
    """Build a backend whose client always answers with the same payload"""
    backend = EventProxyBackend()
    client = CannedClient(backend, **response)
    backend.set_sender(client.send)
    return backend, client


async def in_worker(function: Callable[[], Any]) -> Any:
    """Run ``function`` off the event loop, returning its result or raising its error

    Synchronous live access refuses to block the loop thread, so anything which blocks
    has to run somewhere else - just like the worker thread ReactPy puts plain ``def``
    handlers in.
    """
    outcome: Ref[tuple[bool, Any]] = Ref(None)

    def run() -> None:
        try:
            outcome.current = (True, function())
        except Exception as error:
            outcome.current = (False, error)

    thread = threading.Thread(target=run)
    thread.start()
    await asyncio.to_thread(thread.join, 10)
    assert not thread.is_alive(), "the worker thread never finished"
    succeeded, result = outcome.current
    if not succeeded:
        raise result
    return result


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


async def test_layout_hands_handlers_events_of_their_own_flavour():
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
        return reactpy.html.div({"onSync": sync_handler, "onAsync": async_handler})

    _backend, client = make_client(objects)

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handlers = event_handlers_of(model)

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


async def test_layout_hands_data_which_is_not_a_browser_object_as_is():
    received: dict[str, Any] = {}

    def sync_handler(event):
        received["event"] = event

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": sync_handler})

    _backend, client = make_client(make_objects())

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handlers = event_handlers_of(model)

        target = handlers["onClick"]["target"]
        await layout.deliver(event_message(target, {"type": "click", "detail": 3}))
        await poll(lambda: "event" in received)

    assert type(received["event"]) is Event
    assert received["event"]["type"] == "click"
    assert client.requests == [], "nothing to reach into, so nothing was asked"


async def test_merged_handlers_get_the_flavour_each_needs():
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


async def test_a_handler_which_declines_live_access_takes_the_snapshot():
    """Refusing live access is honoured even while it is on offer

    The mark alongside the data says the browser is still holding whatever the event
    fired from, but a handler which has said it will not reach into the page is not
    handed a proxy on the off chance that it might. It is given the snapshot, and
    nothing is asked of the browser afterwards.
    """
    received: dict[str, Any] = {}

    def handler(event_object):
        received["event"] = event_object

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": event(handler, event_proxy=False)})

    _backend, client = make_client(make_objects())

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handler_spec = event_handlers_of(model)["onClick"]
        assert "eventProxy" not in handler_spec, (
            "a handler which declined was still reported as wanting live access"
        )

        await layout.deliver(
            event_message(
                handler_spec["target"],
                {EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"},
            )
        )
        await poll(lambda: "event" in received)

    assert type(received["event"]) is Event
    assert EVENT_MARKER_KEY not in received["event"]
    assert client.requests == [], "the browser was asked about an event nobody wanted"


async def test_a_handler_which_asks_for_live_access_gets_it():
    """Asking on the handler is enough; the global switch is not needed

    Saying so on the handler does two things: the client is told to hold on to the
    object the event came from, and the server turns the mark the client leaves
    behind into something the handler can actually read through.
    """
    received: dict[str, Any] = {}

    async def handler(event_object):
        received["event"] = event_object

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": event(handler, event_proxy=True)})

    _backend, client = make_client(make_objects())

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handler_spec = event_handlers_of(model)["onClick"]
        assert handler_spec["eventProxy"] is True, (
            "the client was never told to keep the object alive"
        )

        await layout.deliver(
            event_message(
                handler_spec["target"],
                {EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"},
            )
        )
        await poll(lambda: "event" in received)

        assert isinstance(received["event"], AsyncEvent)
        assert await received["event"].read("target.value") == "typed"

    assert requested_paths(client) == [["target", "value"]]


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


# -- what a proxy says about itself -----------------------------------------


async def test_proxies_describe_themselves():
    backend, _client = make_client(make_objects())
    event_object = AsyncEvent(
        backend, "evt", snapshot={"type": "click", 3: "not-an-attribute"}
    )
    target = event_object.target

    assert event_object.backend is backend
    assert event_object.event_id == "evt"
    assert event_object.path == ()
    assert event_object.has_snapshot is True
    assert repr(event_object) == (
        "AsyncEvent(event_id='evt', path=[], "
        "snapshot={'type': 'click', 3: 'not-an-attribute'})"
    )
    # snapshot keys show up as attributes, but only the string ones
    assert "type" in dir(event_object)
    assert "3" not in dir(event_object)

    assert target.backend is backend
    assert target.path == ("target",)
    assert target.has_snapshot is False
    assert repr(target) == (
        "AsyncEventProxy(event_id='evt', path=['target'], snapshot={})"
    )


async def test_internal_attributes_are_never_resolved_against_the_browser():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(backend, "evt", snapshot={})

    for name in ("_reactpy_nothing", "__wrapped__", "__deepcopy__"):
        with pytest.raises(AttributeError, match=f"^{name}$"):
            getattr(event_object, name)

    assert client.requests == [], "internals are not looked up in the browser"


def test_only_the_two_flavours_know_how_to_resolve():
    base = EventProxy(EventProxyBackend(), "evt", ["target"])

    assert dict(base) == {}
    with pytest.raises(NotImplementedError, match="cannot resolve live event data"):
        base._reactpy_resolve_path(False, ())


# -- reading through the snapshot -------------------------------------------


async def test_read_walks_the_whole_dotted_path_at_once():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(
        backend,
        "evt",
        snapshot={
            "target": {"value": "cached"},
            "meta": MappingProxyType({"kind": "mouse", "sub": {"n": 5}}),
            "touches": [{"pageX": 7}, {"pageX": 8}],
        },
    )

    assert await event_object.read("target.value") == "cached"
    assert await event_object.read("meta.kind") == "mouse"
    assert await event_object.read("meta.sub.n") == 5
    assert await event_object.read("touches.1.pageX") == 8
    # a path may be handed over as a sequence too, indices included
    assert await event_object.read(["touches", 0, "pageX"]) == 7
    assert requested_paths(client) == [], "the snapshot answered every one of them"

    # what the snapshot lacks costs exactly one request, however deep it goes
    assert await event_object.read("deep.a.b.c") == 42
    assert requested_paths(client) == [["deep", "a", "b", "c"]]


async def test_read_gives_up_on_paths_the_snapshot_cannot_hold():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(
        backend,
        "evt",
        snapshot={
            "type": "click",
            "meta": MappingProxyType({"kind": "mouse"}),
            "touches": [{"pageX": 7}],
        },
    )

    # strings are not walked into, out of range and non-numeric indices miss too
    assert await event_object.read("type.deeper", default="d1") == "d1"
    assert await event_object.read("meta.absent", default="d2") == "d2"
    assert await event_object.read("touches.9.pageX", default="d3") == "d3"
    assert await event_object.read("touches.first", default="d4") == "d4"

    assert requested_paths(client) == [
        ["type", "deeper"],
        ["meta", "absent"],
        ["touches", "9", "pageX"],
        ["touches", "first"],
    ]
    # without a default the client's refusal is handed straight back
    with pytest.raises(EventProxyNotFound):
        await event_object.read("type.deeper")


async def test_chained_attributes_ask_for_one_level_at_a_time():
    objects = {
        "evt": {
            "chain": Reference(
                {"next": Reference({"next": Reference({"answer": 5})})},
            ),
        },
    }
    backend, client = make_client(objects)
    event_object = SyncEvent(backend, "evt", snapshot={})

    # read() asks for the whole path in a single round trip ...
    assert await in_worker(lambda: event_object.read("chain.next.next.answer")) == 5
    assert requested_paths(client) == [["chain", "next", "next", "answer"]]

    # ... while walking attributes resolves whatever the last answer left over
    client.sent.clear()
    assert await in_worker(lambda: event_object.chain.next.next.answer) == 5
    assert requested_paths(client) == [
        ["chain"],
        ["chain", "next"],
        ["chain", "next", "next"],
        ["chain", "next", "next", "answer"],
    ]


# -- snapshot data which is a reference or a list ---------------------------


async def test_references_inside_a_snapshot_become_real_proxies():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(
        backend,
        "evt",
        snapshot={
            "node": {
                EVENT_REFERENCE_KEY: {
                    "path": ["target"],
                    "callable": True,
                    "eventId": "other",
                }
            },
            "self_ref": {EVENT_REFERENCE_KEY: {}},
        },
    )

    node = event_object.node
    assert isinstance(node, AsyncEventProxy)
    # the path the client handed us wins over where this proxy sits
    assert node.path == ("target",)
    assert node.event_id == "other"
    assert node._reactpy_callable is True, "the client said this one is a function"
    assert EVENT_REFERENCE_KEY not in dict(node)

    # a reference which does not say where it points at keeps our own path
    self_ref = event_object.self_ref
    assert isinstance(self_ref, AsyncEventProxy)
    assert self_ref.path == ("self_ref",)
    assert self_ref.event_id == "evt"
    assert self_ref._reactpy_callable is False
    assert requested_paths(client) == []


async def test_lists_inside_a_snapshot_are_wrapped_with_child_proxies():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(
        backend,
        "evt",
        snapshot={
            "touches": [{"pageX": 1}, {"pageX": 2}],
            "matrix": [[{"x": 1}], [3, "four"], None],
        },
    )

    touches = event_object.touches
    assert [touch["pageX"] for touch in touches] == [1, 2]
    assert [touch.path for touch in touches] == [
        ("touches", "0"),
        ("touches", "1"),
    ]
    assert all(isinstance(touch, AsyncEventProxy) for touch in touches)

    matrix = event_object.matrix
    assert isinstance(matrix[0][0], AsyncEventProxy)
    assert matrix[0][0].path == ("matrix", "0", "0")
    assert matrix[0][0]["x"] == 1
    assert matrix[1] == [3, "four"]
    assert matrix[2] is None
    assert requested_paths(client) == []


# -- the dict protocol of an asynchronous proxy -----------------------------


async def test_async_proxies_refuse_to_be_inspected_while_unknown():
    backend, client = make_client(make_objects())
    target = AsyncEventProxy(backend, "evt", ["target"])

    with pytest.raises(EventProxyAccessError) as measure:
        len(target)
    assert "cannot measure AsyncEventProxy for ['target'] of event 'evt'" in str(
        measure.value
    )
    assert "await the proxy" in str(measure.value)

    with pytest.raises(EventProxyAccessError, match="cannot iterate over"):
        iter(target)
    with pytest.raises(EventProxyAccessError, match="cannot test membership of"):
        assert "type" in target

    assert requested_paths(client) == []

    # once the client has told us something the dict protocol is free
    event_object = AsyncEvent(backend, "evt", snapshot={"type": "click"})
    assert len(event_object) == 1
    assert list(event_object) == ["type"]
    assert "type" in event_object
    assert "target" not in event_object
    assert requested_paths(client) == []


async def test_proxies_without_a_connection_are_quietly_empty():
    event_object = AsyncEvent(EventProxyBackend(), "evt", snapshot={})

    assert len(event_object) == 0
    assert list(event_object) == []
    assert "type" not in event_object


# -- what the synchronous flavour does when it has to block -----------------


async def test_sync_reads_either_use_the_snapshot_or_block_for_the_browser():
    objects = make_objects()
    objects["evt"]["detail"] = 7
    backend, client = make_client(objects)
    event_object = SyncEvent(backend, "evt", snapshot={"type": "click"})

    def access():
        return (
            event_object.read("type"),
            event_object.read("target.value"),
            event_object.read("nope", default="fallback"),
            event_object.detail,
            SyncEventProxy(backend, "evt", ["target"]).resolve(),
        )

    cached, typed, fallback, detail, resolved = await in_worker(access)
    assert (cached, typed, fallback, detail) == ("click", "typed", "fallback", 7)
    assert type(resolved) is dict
    assert resolved["value"] == "typed"
    assert requested_paths(client) == [
        ["target", "value"],
        ["nope"],
        ["detail"],
        ["target"],
    ]

    # without a default the client's refusal is raised rather than swallowed
    with pytest.raises(EventProxyNotFound):
        await in_worker(lambda: event_object.read("nope"))


async def test_sync_reads_the_browser_cannot_answer_degrade_to_a_blank_proxy():
    backend, client = make_client(make_objects())
    event_object = SyncEvent(backend, "evt", snapshot={})

    with assert_reactpy_did_log("Falling back to snapshot data", EventProxyNotFound):
        missing = await in_worker(lambda: event_object.nope)
    assert isinstance(missing, SyncEventProxy)
    assert missing.path == ("nope",)
    assert missing.has_snapshot is False
    assert requested_paths(client) == [["nope"]]

    # printing and iterating still work, so a failed read is safe to log
    with assert_reactpy_did_log("Could not resolve", EventProxyNotFound):
        assert await in_worker(lambda: str(missing)) == "{}"
        empty = await in_worker(lambda: iter(missing))
        assert next(empty, None) is None
    assert requested_paths(client) == [["nope"], ["nope"], ["nope"]]


async def test_sync_proxies_compare_by_what_they_point_at():
    objects = make_objects()
    objects["evt"]["numbers"] = [1, 2, 3]
    backend, _client = make_client(objects)
    left = SyncEventProxy(backend, "evt", ["target"], snapshot={"k": 1})
    same = SyncEventProxy(backend, "evt", ["target"], snapshot={"k": 2})
    other = SyncEventProxy(backend, "evt", ["deep"], snapshot={"k": 2})

    # the very same browser object, whatever either snapshot happens to say
    assert (left == same) is True
    assert (left != same) is False
    # a different path leaves it to the data we hold
    assert (left == other) is False
    assert (left != other) is True
    assert (left == SyncEventProxy(backend, "evt", ["deep"], {"k": 1})) is True

    # against anything else the live value is what counts
    numbers = SyncEventProxy(backend, "evt", ["numbers"])
    assert await in_worker(lambda: numbers == [1, 2, 3]) is True
    assert await in_worker(lambda: numbers == [1, 2]) is False
    assert await in_worker(lambda: numbers != [1, 2, 3]) is False

    # a snapshot we already have is never compared against the browser
    answered = SyncEventProxy(backend, "evt", ["x"], snapshot={"k": 1})
    assert await in_worker(lambda: answered == 5) is False
    assert await in_worker(lambda: answered != 5) is True


async def test_sync_proxies_print_and_measure_like_their_values():
    objects = make_objects()
    objects["evt"]["numbers"] = [1, 2, 3]
    backend, _client = make_client(objects)
    numbers = SyncEventProxy(backend, "evt", ["numbers"])
    node = SyncEventProxy(backend, "evt", ["target"])
    answered = SyncEventProxy(backend, "evt", ["x"], snapshot={"k": 1})

    assert await in_worker(lambda: str(numbers)) == "[1, 2, 3]"
    assert await in_worker(lambda: format(numbers, "")) == "[1, 2, 3]"
    assert await in_worker(lambda: str(answered)) == "{'k': 1}"
    assert await in_worker(lambda: format(answered, "")) == "{'k': 1}"

    assert await in_worker(lambda: len(numbers)) == 3
    assert await in_worker(lambda: list(numbers)) == [1, 2, 3]
    assert await in_worker(lambda: len(answered)) == 1
    assert await in_worker(lambda: list(answered)) == ["k"]

    assert await in_worker(lambda: 2 in numbers) is True
    assert await in_worker(lambda: 9 in numbers) is False
    assert await in_worker(lambda: "tagName" in node) is True
    assert await in_worker(lambda: "k" in answered) is True
    assert await in_worker(lambda: "zzz" in answered) is False

    # a reference to something else says nothing about this proxy
    deep = SyncEventProxy(backend, "evt", ["deep"])
    assert await in_worker(lambda: str(deep)) == "{}"
    deep_items = await in_worker(lambda: iter(deep))
    assert next(deep_items, None) is None

    # a read which failed is simply "not there"
    missing = SyncEventProxy(backend, "evt", ["nope"])
    assert await in_worker(lambda: "anything" in missing) is False
    # with no connection at all membership is never asked of the browser
    offline = SyncEventProxy(EventProxyBackend(), "evt", ["target"])
    assert ("tagName" in offline) is False


# -- when the connection is not what it should be ---------------------------


async def test_a_failed_send_switches_live_access_off():
    backend = EventProxyBackend()
    sent: list[dict[str, Any]] = []

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)
        msg = "socket is closed"
        raise ConnectionResetError(msg)

    backend.set_sender(send)
    event_object = AsyncEvent(backend, "evt", snapshot={})

    with pytest.raises(EventProxyUnavailable, match="failed to send"):
        await event_object.read("target")

    assert len(sent) == 1, "the request was handed to the client once"
    assert backend.disabled
    assert not backend.available


async def test_closing_the_backend_fails_everything_still_in_flight():
    backend, client = make_client(make_objects(), respond=False)
    event_object = AsyncEvent(backend, "evt", snapshot={})
    pending = [
        asyncio.create_task(event_object.read("target")),
        asyncio.create_task(event_object.read("type")),
    ]
    await poll(lambda: len(client.requests) == 2)

    backend.close()

    for task in pending:
        with pytest.raises(EventProxyUnavailable, match="layout was closed"):
            await task
    # the answers of a client which turns up late are simply dropped
    assert client.backend.handle_response(
        {
            "type": EVENT_PROXY_RESPONSE_TYPE,
            "requestId": client.requests[0]["requestId"],
            "ok": True,
            "value": "too late",
        }
    )


async def test_blocking_reads_time_out(monkeypatch):
    monkeypatch.setattr(REACTPY_EVENT_PROXY_TIMEOUT, "current", 0.05)
    monkeypatch.setattr(REACTPY_EVENT_PROXY_MAX_TIMEOUTS, "current", 1)
    backend, client = make_client(make_objects(), respond=False)
    event_object = SyncEvent(backend, "evt", snapshot={})

    with pytest.raises(EventProxyTimeout, match="did not answer"):
        await in_worker(lambda: event_object.read("target"))

    assert len(client.requests) == 1
    assert backend.disabled


async def test_client_reported_timeouts_count_against_the_same_budget(monkeypatch):
    monkeypatch.setattr(REACTPY_EVENT_PROXY_MAX_TIMEOUTS, "current", 1)
    backend, _client = make_canned_client(
        ok=False, code="timeout", error="browser hung"
    )
    event_object = AsyncEvent(backend, "evt", snapshot={})

    with pytest.raises(EventProxyTimeout, match="did not answer"):
        await event_object.read("target")

    assert backend.disabled, "a timeout the client reports is still a timeout"


async def test_failures_the_client_cannot_explain_are_still_reported():
    backend, client = make_canned_client(ok=False)
    event_object = AsyncEvent(backend, "evt", snapshot={})

    with pytest.raises(EventProxyAccessError) as info:
        await event_object.read("target")

    assert "could not resolve ['target'] of event 'evt'" in str(info.value)
    assert "the client did not provide a reason" in str(info.value)
    assert not backend.disabled, "one refusal is not a broken connection"
    assert len(client.requests) == 1


async def test_requests_made_just_after_the_loop_is_gone_fail_fast(monkeypatch):
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(backend, "evt", snapshot={})
    loop = asyncio.get_running_loop()
    # the loop which owned this connection has gone away, the sender has not noticed
    monkeypatch.setattr(backend, "_loop", None)

    with pytest.raises(EventProxyUnavailable, match="no sender is bound"):
        await event_object.read("target")

    assert client.sent == [], "nothing was handed over a loop which no longer runs"
    monkeypatch.setattr(backend, "_loop", loop)
    # the request was dropped rather than left behind waiting for an answer
    assert await event_object.read("target.value") == "typed"


# -- calls the client may or may not have to answer -------------------------


async def test_fires_and_forget_calls_never_raise_at_the_handler():
    # nothing is bound to this backend, so there is nobody to tell
    event_object = AsyncEvent(EventProxyBackend(), "evt", snapshot={})

    assert event_object.preventDefault() is None
    assert event_object.stopPropagation() is None
    assert event_object.stopImmediatePropagation() is None

    # what we asked for is still recorded, only the browser side call is dropped
    assert event_object.defaultPrevented is True
    assert event_object.propagationStopped is True


async def test_stop_immediate_propagation_is_forwarded_to_the_client():
    objects = make_objects()
    objects["evt"]["stopImmediatePropagation"] = Method()
    backend, client = make_client(objects)
    event_object = AsyncEvent(backend, "evt", snapshot={})

    event_object.stopImmediatePropagation()

    await poll(lambda: len(client.requests) == 1)
    assert requested_paths(client) == [["stopImmediatePropagation"]]
    assert client.requests[0]["reply"] is False
    assert objects["evt"]["stopImmediatePropagation"].calls == [()]
    assert event_object.propagationStopped is True
    assert event_object.defaultPrevented is False


async def test_client_side_calls_can_be_waited_for():
    objects = make_objects()
    backend, client = make_client(objects)
    target = AsyncEventProxy(backend, "evt", ["target"])

    # ``preventDefault()`` and friends do not wait; asking to wait hands back
    # whatever the browser's method returned once it has actually run
    assert await target._reactpy_invoke("focus", (), wait=True) == "focused"

    assert objects["evt"]["target"]["focus"].calls == [()]
    assert requested_paths(client) == [["target", "focus"]]
    assert client.requests[0]["reply"] is True


async def test_the_event_object_itself_cannot_be_called():
    backend, client = make_client(make_objects())
    event_object = AsyncEvent(backend, "evt", snapshot={})

    with pytest.raises(EventProxyAccessError, match="cannot be called"):
        await event_object()
    with pytest.raises(EventProxyAccessError, match="cannot be called"):
        await AsyncEventProxy(backend, "evt")()

    # ... and the blocking flavour says the same thing from a worker thread
    def call_the_root():
        return SyncEvent(backend, "evt", snapshot={})()

    with pytest.raises(EventProxyAccessError, match="cannot be called"):
        await in_worker(call_the_root)

    assert client.requests == []


# -- how event data is recognised and handed out ----------------------------


async def test_a_plain_string_marker_names_a_live_event_too():
    backend, _client = make_client(make_objects())

    args, flavor = build_event_args(
        [{EVENT_MARKER_KEY: "evt", "type": "click"}, {"type": "click"}, "extra"],
        backend,
    )

    assert isinstance(args[0], AsyncEvent)
    assert args[0].event_id == "evt"
    assert args[0]["type"] == "click"
    assert type(args[1]) is Event
    assert args[2] == "extra"
    assert flavor is True

    sync_args, sync_flavor = build_event_args(
        [{EVENT_MARKER_KEY: {"id": "evt"}}], backend, prefer_async=False
    )
    assert isinstance(sync_args[0], SyncEvent)
    assert sync_flavor is False


def test_arguments_the_client_could_never_use_are_refused():
    assert serialize_argument(("a", "b")) == ["a", "b"]
    for value in (b"bytes", bytearray(b"raw"), {1, 2}, object()):
        with pytest.raises(EventProxyAccessError, match="cannot pass"):
            serialize_argument(value)
