"""Tests for the live, client backed event objects in :mod:`reactpy._event_proxy`.

Nothing about the object behind an event is sent to the server when it is dispatched.
The client keeps it alive and sends only an id, so every property a handler reads is a
round trip, and most of what follows counts those round trips.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from time import monotonic
from typing import Any

import pytest

import reactpy
from reactpy._event_proxy import (
    EVENT_MARKER_KEY,
    EVENT_PROXY_REQUEST_TYPE,
    EVENT_PROXY_RESPONSE_TYPE,
    EVENT_REFERENCE_KEY,
    Event,
    EventProxy,
    EventProxyAccessError,
    EventProxyBackend,
    EventProxyError,
    EventProxyNotFound,
    EventProxyTimeout,
    EventProxyUnavailable,
    build_event_args,
    deserialize_value,
    serialize_argument,
)
from reactpy.config import (
    REACTPY_EVENT_PROXY_MAX_TIMEOUTS,
    REACTPY_EVENT_PROXY_TIMEOUT,
)
from reactpy.core.component import component
from reactpy.core.events import EventHandler, merge_event_handlers
from reactpy.core.layout import Layout
from tests.tooling.common import event_message


def make_event(
    backend: EventProxyBackend,
    event_id: str,
    known: dict[str, Any] | None = None,
    path: Sequence[str | int] = (),
) -> Event:
    """Build an event the way the layout hands one to a handler"""
    return Event(backend=backend, event_id=event_id, path=path, known=known)


def make_proxy(
    backend: EventProxyBackend,
    event_id: str,
    path: Sequence[str | int] = (),
    known: dict[str, Any] | None = None,
) -> EventProxy:
    """Build a member proxy of the kind an event hands out"""
    return EventProxy(backend=backend, event_id=event_id, path=path, known=known)


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
        """Every individual request which went out, batched together or not"""
        found: list[dict[str, Any]] = []
        for message in self.messages:
            batch = message.get("requests")
            if isinstance(batch, list):
                found.extend(batch)
            else:
                found.append(message)
        return found

    @property
    def messages(self) -> list[dict[str, Any]]:
        """The request messages exactly as they left the process"""
        return [m for m in self.sent if m["type"] == EVENT_PROXY_REQUEST_TYPE]

    async def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)
        if message["type"] != EVENT_PROXY_REQUEST_TYPE or not self.respond:
            return
        loop = asyncio.get_running_loop()
        batch = message.get("requests")
        work = (
            [dict(entry) for entry in batch]
            if isinstance(batch, list)
            else [dict(message)]
        )
        if self.delay > 0:
            loop.call_later(self.delay, self._answer, work)
        else:
            # Carried out within this same turn of the loop. A zero-delay timer is
            # due "now" but is only picked up on a later turn, and a loop with a
            # coarse clock (Windows) can let a test read ahead of that turn.
            loop.call_soon(self._answer, work)

    def _answer(self, messages: list[dict[str, Any]]) -> None:
        """Reply to a whole batch at once, the way the browser answers one request

        Requests which did not ask for a reply go unanswered, so a batch of nothing but
        fire-and-forget calls sends no message back at all.
        """
        replies = [
            reply
            for reply in (self._reply_for(message) for message in messages)
            if reply is not None
        ]
        if not replies:
            return
        if len(replies) == 1:
            self.backend.handle_response(replies[0])
            return
        self.backend.handle_response(
            {"type": EVENT_PROXY_RESPONSE_TYPE, "responses": replies},
        )

    def _reply_for(self, message: dict[str, Any]) -> dict[str, Any] | None:
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
            return response if should_reply else None

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
        return response if should_reply else None

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
        found: list[dict[str, Any]] = []
        for message in self.sent:
            if message["type"] != EVENT_PROXY_REQUEST_TYPE:
                continue
            batch = message.get("requests")
            found.extend(batch if isinstance(batch, list) else [message])
        return found

    async def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)
        if message["type"] != EVENT_PROXY_REQUEST_TYPE:
            return
        batch = message.get("requests")
        asking = [
            entry
            for entry in (batch if isinstance(batch, list) else [message])
            if entry.get("reply")
        ]
        if not asking:
            return
        answers = [
            {
                "requestId": entry["requestId"],
                "ok": self.ok,
                "value": self.value,
                "error": self.error,
                "code": self.code,
            }
            for entry in asking
        ]
        if len(answers) == 1:
            self.backend.handle_response(
                {"type": EVENT_PROXY_RESPONSE_TYPE, **answers[0]},
            )
            return
        self.backend.handle_response(
            {"type": EVENT_PROXY_RESPONSE_TYPE, "responses": answers},
        )


def make_canned_client(**response: Any) -> tuple[EventProxyBackend, CannedClient]:
    """Build a backend whose client always answers with the same payload"""
    backend = EventProxyBackend()
    client = CannedClient(backend, **response)
    backend.set_sender(client.send)
    return backend, client


# -- every proxy is awaitable, whether or not its value is already known -----


async def read_it_the_way_a_handler_does(event_object: Event) -> tuple[Any, Any]:
    """The very expressions a handler writes, run against either kind of event

    Under the snapshot model this could only be written for one of them: awaiting
    ``event.type`` raised ``TypeError: object str can't be used in 'await'
    expression`` whenever the client had happened to include the type with the event,
    because the snapshot handed back the bare string. Both events below are read with
    the same awaits and answer the same; only what they cost differs.
    """
    return await event_object.type, await event_object.target.value


async def test_every_proxy_is_awaitable_whether_the_value_is_known_or_not():
    backend, client = make_client(make_objects())
    nothing_is_known = make_event(backend, "evt")

    assert type(nothing_is_known) is Event
    assert await read_it_the_way_a_handler_does(nothing_is_known) == ("click", "typed")
    assert requested_paths(client) == [["type"], ["target", "value"]]

    backend, client = make_client(make_objects())
    the_type_is_known = make_event(backend, "evt", known={"type": "click"})

    assert type(the_type_is_known) is Event
    assert await the_type_is_known.type == "click"
    assert client.messages == [], "a value the client volunteered is never asked for"
    assert await read_it_the_way_a_handler_does(the_type_is_known) == (
        "click",
        "typed",
    )
    assert requested_paths(client) == [
        ["target", "value"]
    ], "one round trip for the one property which was not known"

    # a known value is still a proxy rather than the bare value, so awaiting it is
    # neither optional nor forbidden - it simply costs nothing
    assert isinstance(the_type_is_known.type, EventProxy)
    assert the_type_is_known.type.is_known is True
    assert nothing_is_known.target.is_known is False


async def test_a_known_member_costs_no_round_trip():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt", known={"type": "click"})

    assert await event_object.type == "click"
    assert (await event_object.read("type")) == ("click",)
    assert requested_paths(client) == []
    assert "type" in dir(event_object), "a known member should still be discoverable"

    # a value handed over up front is awaitable at the path it belongs to as well
    handed_over = EventProxy(
        backend=backend, event_id="evt", path=("target", "value"), value="typed"
    )
    assert await handed_over == "typed"
    assert requested_paths(client) == []


async def test_a_property_is_read_from_the_browser_only_once():
    """A resolved property is cached against its event, however it is spelled"""
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    assert await event_object.target.value == "typed"
    assert (await event_object.read("target.value")) == ("typed",)
    assert await event_object.target.value == "typed"

    assert requested_paths(client) == [
        ["target", "value"]
    ], "the browser was asked about one property exactly once"
    assert len(client.messages) == 1


async def test_reads_which_are_in_flight_together_travel_as_one_message():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    value, tag_name = await event_object.read("target.value", "target.tagName")

    assert (value, tag_name) == ("typed", "INPUT"), "answers arrive in the asked order"
    assert len(client.messages) == 1, "both reads left the process together"
    message = client.messages[0]
    assert [entry["path"] for entry in message["requests"]] == [
        ["target", "value"],
        ["target", "tagName"],
    ]
    assert requested_paths(client) == [["target", "value"], ["target", "tagName"]]


async def test_gathered_reads_are_batched():
    """``asyncio.gather`` of several reads costs one round trip, not several"""
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    value, tag_name = await asyncio.gather(
        event_object.target.value, event_object.target.tagName
    )

    assert (value, tag_name) == ("typed", "INPUT")
    assert len(client.messages) == 1
    assert len(client.requests) == 2


async def test_sequential_reads_are_not_batched():
    """The honest limitation, so nobody optimises it into a lie

    Two ``await`` expressions written one after the other cannot travel together: the
    second is not even thought of until the first has landed.
    """
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    assert await event_object.target.value == "typed"
    assert await event_object.target.tagName == "INPUT"

    assert len(client.messages) == 2
    assert requested_paths(client) == [["target", "value"], ["target", "tagName"]]


async def test_a_read_already_in_flight_is_shared_rather_than_duplicated():
    """Two readers of one property send one request

    The second does not ask the browser again and does not collect an answer of its
    own; it waits on the request which is already on its way. Sharing has to outlast
    the queueing of a request, so the read is remembered as in flight until the answer
    has been delivered - which is also what stops a timed out request from being
    joined by anyone later.
    """
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    value, again = await asyncio.gather(
        event_object.target.value, event_object.target.value
    )

    assert value == again == "typed"
    assert requested_paths(client) == [
        ["target", "value"]
    ], "the browser was asked once for what two readers wanted"
    assert len(client.messages) == 1


async def test_a_batch_adopts_a_read_which_is_already_in_flight():
    """A batch does not re-ask for what a lone read is already waiting on"""
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    lone = asyncio.ensure_future(event_object.target.value)
    await asyncio.sleep(0)  # let it set off, and register itself as in flight

    value, tag_name = await event_object.read("target.value", "target.tagName")

    assert await lone == value == "typed", "both readers got the one answer"
    assert tag_name == "INPUT"
    assert requested_paths(client) == [
        ["target", "value"],
        ["target", "tagName"],
    ], "the batch asked only for the property nobody had asked about yet"


async def test_read_of_no_paths_returns_an_empty_tuple():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    assert await event_object.read() == ()
    assert requested_paths(client) == []


async def test_a_proxy_is_not_a_container():
    """A proxy is not a mapping, and must never be made to look like one

    ``EventProxy`` deliberately has no ``__getitem__``, ``__len__``, ``__iter__`` or
    ``__contains__``. The trap which hung the test suite is defining ``__getitem__``
    without ``__iter__``: ``x in proxy`` then falls back to trying ``proxy[0]``,
    ``proxy[1]``, ... until an index raises ``IndexError``, and for a proxy no index is
    ever missing - every one of them hands back another proxy - so the membership test
    spun forever. There is nothing to enumerate about an object which is still sitting
    in the browser anyway.
    """
    backend, _client = make_client(make_objects())
    event_object = make_event(backend, "evt", known={"type": "click"})

    for name in ("__getitem__", "__len__", "__iter__", "__contains__"):
        assert not hasattr(EventProxy, name), f"{name} would make a proxy enumerable"

    with pytest.raises(TypeError):
        event_object["target"]
    with pytest.raises(TypeError):
        "type" in event_object
    with pytest.raises(TypeError):
        len(event_object)
    with pytest.raises(TypeError):
        list(event_object)


async def test_a_proxy_is_always_truthy():
    """A proxy stands for its browser object even before that object is known

    ``bool`` answers True without leaving the process, so ``if event.target:`` cannot
    quietly drop an element whose value turns out to be an empty string, a zero or
    :data:`None`. What is unknown is not the same as absent.
    """
    backend, _client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    assert bool(event_object) is True
    assert bool(event_object.target) is True


async def test_the_debounce_a_handler_sets_can_be_read_back():
    """``debounce`` is a setting on the handler rather than a trip to the browser"""
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    assert event_object.debounce is None

    event_object.debounce = 150

    assert event_object.debounce == 150
    assert client.messages == [], "a setting the server keeps costs nothing"


# -- what a proxy says about itself -----------------------------------------


async def test_proxies_describe_themselves():
    backend, _client = make_client(make_objects())
    event_object = make_event(backend, "evt", known={"type": "click"})
    target = event_object.target

    assert event_object.backend is backend
    assert event_object.event_id == "evt"
    assert event_object.path == ()
    assert repr(event_object) == "Event(event_id='evt', path=[])"
    # what the client volunteered shows up as a member, and nothing else does
    assert "type" in dir(event_object)
    assert "target" not in dir(event_object)

    assert target.backend is backend
    assert target.path == ("target",)
    assert repr(target) == "EventProxy(event_id='evt', path=['target'])"

    # there is no positional snapshot argument to hand over any more
    with pytest.raises(TypeError):
        EventProxy(backend, "evt")


async def test_internal_attributes_are_never_resolved_against_the_browser():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    for name in ("_reactpy_nothing", "__wrapped__", "__deepcopy__"):
        with pytest.raises(AttributeError, match=f"^{name}$"):
            getattr(event_object, name)

    assert client.requests == [], "internals are not looked up in the browser"


async def test_a_proxy_with_nothing_behind_it_cannot_resolve():
    base = make_proxy(EventProxyBackend(), "evt", ["target"])

    assert repr(base) == "EventProxy(event_id='evt', path=['target'])"
    assert base.is_known is False
    with pytest.raises(EventProxyUnavailable, match="live access"):
        await base


# -- reading and calling through a proxy -------------------------------------


async def test_read_walks_the_whole_dotted_path_at_once():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    assert (await event_object.read("target.value")) == ("typed",)
    assert (await event_object.read("target.tagName")) == ("INPUT",)
    # a chain is asked for as one path, however deep it goes ...
    assert (await event_object.read("deep.a.b.c")) == (42,)
    # ... and may be handed over as a sequence of segments too, indices included
    assert (await event_object.read(["touches", 0, "pageX"])) == (1,)
    assert (await event_object.read("touches.1.pageX")) == (2,)

    assert requested_paths(client) == [
        ["target", "value"],
        ["target", "tagName"],
        ["deep", "a", "b", "c"],
        ["touches", "0", "pageX"],
        ["touches", "1", "pageX"],
    ]


async def test_reads_use_what_is_known_and_ask_for_everything_else():
    objects = make_objects()
    objects["evt"]["detail"] = 7
    backend, client = make_client(objects)
    event_object = make_event(backend, "evt", known={"type": "click"})

    cached = await event_object.read("type")
    typed = await event_object.read("target.value")
    detail = await event_object.read("detail")
    resolved = await make_proxy(backend, "evt", ["target"]).resolve()

    assert cached == ("click",)
    assert typed == ("typed",)
    assert detail == (7,)
    assert type(resolved) is dict, "a plain object comes back as a plain object"
    assert resolved["value"] == "typed"
    assert requested_paths(client) == [
        ["target", "value"],
        ["detail"],
        ["target"],
    ]

    # a path the browser does not have is raised, never quietly answered with None
    with pytest.raises(EventProxyNotFound):
        await event_object.read("nope")
    assert requested_paths(client)[-1] == ["nope"]


async def test_chained_attributes_are_asked_for_in_one_round_trip():
    def chain(answer: int) -> Reference:
        return Reference({"next": Reference({"next": Reference({"answer": answer})})})

    objects = {"evt": {"chain": chain(5), "trail": chain(7)}}
    backend, client = make_client(objects)
    event_object = make_event(backend, "evt")

    # read() asks for the whole path in a single round trip ...
    assert (await event_object.read("chain.next.next.answer")) == (5,)
    assert requested_paths(client) == [["chain", "next", "next", "answer"]]

    # ... and so does walking attributes, since nothing is asked of the browser until
    # the value behind the last name in the chain is actually awaited. A chain four
    # names deep costs one request here, not one request per name.
    assert await event_object.trail.next.next.answer == 7
    assert requested_paths(client) == [
        ["chain", "next", "next", "answer"],
        ["trail", "next", "next", "answer"],
    ]

    # either of them again sends nothing at all, spelled whichever way
    assert await event_object.trail.next.next.answer == 7
    assert (await event_object.read("chain.next.next.answer")) == (5,)
    assert len(client.messages) == 2


async def test_async_event_walks_references():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    deep = await event_object.deep.resolve()
    assert isinstance(deep, EventProxy)
    assert deep.path == ("deep",)
    assert await event_object.deep.a.b.c == 42
    # the same path spelled the other way is answered out of the cache the backend
    # keeps against (event id, path), so it costs the browser nothing at all
    assert (await event_object.read("deep.a.b.c")) == (42,)
    assert requested_paths(client) == [["deep"], ["deep", "a", "b", "c"]]


async def test_async_event_calls_client_side_methods():
    objects = make_objects()
    backend, _client = make_client(objects)
    event_object = make_event(backend, "evt")

    assert await event_object.target.focus() == "focused"
    assert await event_object.composedPath() == ["window", "input"]
    assert objects["evt"]["target"]["focus"].calls == [()]

    await event_object.log(event_object.target, {"a": [1, 2]})
    logged_node, payload = objects["evt"]["log"].calls[-1]
    assert logged_node["tagName"] == "INPUT"
    assert logged_node["value"] == "typed"
    assert payload == {"a": [1, 2]}


async def test_missing_objects_and_paths_are_reported():
    backend, _client = make_client(make_objects())
    missing = make_event(backend, "not-registered")
    with pytest.raises(EventProxyNotFound):
        await missing.resolve()

    event_object = make_event(backend, "evt")
    with pytest.raises(EventProxyNotFound):
        await event_object.nope.resolve()


async def test_the_event_object_itself_cannot_be_called():
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    with pytest.raises(EventProxyAccessError, match="cannot be called"):
        await event_object()
    with pytest.raises(EventProxyAccessError, match="cannot be called"):
        await make_proxy(backend, "evt")()

    assert client.requests == []


async def test_client_side_calls_can_be_waited_for():
    objects = make_objects()
    backend, client = make_client(objects)
    target = make_proxy(backend, "evt", ["target"])

    # ``preventDefault()`` and friends do not wait; asking to wait hands back
    # whatever the browser's method returned once it has actually run
    assert await target._reactpy_invoke("focus", (), wait=True) == "focused"

    assert objects["evt"]["target"]["focus"].calls == [()]
    assert requested_paths(client) == [["target", "focus"]]
    assert client.requests[0]["reply"] is True


async def test_fires_and_forget_calls_never_raise_at_the_handler():
    # nothing is bound to this backend, so there is nobody to tell
    event_object = make_event(EventProxyBackend(), "evt")

    assert event_object.preventDefault() is None
    assert event_object.stopPropagation() is None
    assert event_object.stopImmediatePropagation() is None

    # what we asked for is still recorded, only the browser side call is dropped
    assert event_object.defaultPrevented is True
    assert event_object.propagationStopped is True


async def test_prevent_default_is_scheduled_but_not_awaited():
    objects = make_objects()
    backend, client = make_client(objects)
    event_object = make_event(backend, "evt")

    event_object.preventDefault()
    event_object.stopPropagation()
    assert event_object.defaultPrevented
    assert event_object.propagationStopped

    # Wait on the calls themselves rather than on how many requests went out: the
    # fake client carries a request out a turn after it records sending it, and a
    # loop with a coarser clock (Windows) lets this test read ahead of that turn.
    prevented, stopped = (
        objects["evt"]["preventDefault"],
        objects["evt"]["stopPropagation"],
    )
    await poll(lambda: len(prevented.calls) == 1 and len(stopped.calls) == 1)
    assert requested_paths(client) == [["preventDefault"], ["stopPropagation"]]
    assert all(not request["reply"] for request in client.requests)
    assert prevented.calls == [()]
    assert stopped.calls == [()]


async def test_stop_immediate_propagation_is_forwarded_to_the_client():
    objects = make_objects()
    objects["evt"]["stopImmediatePropagation"] = Method()
    backend, client = make_client(objects)
    event_object = make_event(backend, "evt")

    event_object.stopImmediatePropagation()

    stop_immediately = objects["evt"]["stopImmediatePropagation"]
    await poll(lambda: len(stop_immediately.calls) == 1)
    assert requested_paths(client) == [["stopImmediatePropagation"]]
    assert client.requests[0]["reply"] is False
    assert stop_immediately.calls == [()]
    assert event_object.propagationStopped is True
    assert event_object.defaultPrevented is False


# -- what may cross the connection in either direction -----------------------


def test_arguments_are_serialized_or_refused():
    backend = EventProxyBackend()
    proxy = make_proxy(backend, "evt", ["target"])
    assert serialize_argument(proxy) == {
        EVENT_REFERENCE_KEY: {"eventId": "evt", "path": ["target"]},
    }
    assert serialize_argument({"a": [1, "two", None]}) == {"a": [1, "two", None]}
    with pytest.raises(EventProxyAccessError):
        serialize_argument(object())


def test_arguments_the_client_could_never_use_are_refused():
    assert serialize_argument(("a", "b")) == ["a", "b"]
    for value in (b"bytes", bytearray(b"raw"), {1, 2}, object()):
        with pytest.raises(EventProxyAccessError, match="cannot pass"):
            serialize_argument(value)


def test_excessively_nested_references_are_refused():
    backend = EventProxyBackend()
    value: Any = {EVENT_REFERENCE_KEY: {"path": ["a"]}}
    for _ in range(20):
        value = {"nested": value}

    with pytest.raises(EventProxyAccessError):
        deserialize_value(value, "evt", backend)


# -- when there is nobody on the other end to answer -------------------------


def test_backend_without_a_sender_is_unavailable():
    backend = EventProxyBackend()
    assert not backend.available

    data = [{EVENT_MARKER_KEY: {"id": "evt"}, "type": "click"}, 5]
    args = build_event_args(data, backend)
    assert isinstance(args[0], Event)
    assert args[1] == 5


async def test_a_request_whose_sender_went_away_is_abandoned():
    """Losing the connection between queueing and sending strands nobody

    Requests leave together at the end of a pass round the loop, so there is a moment
    when a request is committed but the browser has not been asked. If the way to the
    client disappears in that moment the waiter is told plainly, rather than being
    left to sit on a request which will never be sent.
    """
    backend, _client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    pending = asyncio.ensure_future(event_object.target.value)
    await asyncio.sleep(0)  # the request is queued, waiting for the flush to carry it

    backend._send = None  # the connection went away before the queue was drained
    backend._flush()

    with pytest.raises(EventProxyUnavailable):
        await pending


def test_a_response_before_the_layout_runs_has_nobody_to_wake():
    """An answer arriving outside the layout's life has no request to satisfy

    The backend belongs to the running layout, so before it has started - or after it
    has stopped - there is nothing to hand the answer to. It is refused rather than
    raising, because the connection has no way to know the difference and should not
    be blamed for the timing.
    """

    @component
    def MyComponent():
        return reactpy.html.div()

    layout = Layout(MyComponent())

    assert (
        layout.handle_event_proxy_response(
            {"type": EVENT_PROXY_RESPONSE_TYPE, "requestId": "gone", "ok": True}
        )
        is False
    )


async def test_unanswered_requests_eventually_disable_live_access(monkeypatch):
    monkeypatch.setattr(REACTPY_EVENT_PROXY_TIMEOUT, "current", 0.05)
    monkeypatch.setattr(REACTPY_EVENT_PROXY_MAX_TIMEOUTS, "current", 2)
    backend, _client = make_client(make_objects(), respond=False)
    event_object = make_event(backend, "evt")

    # Each attempt asks for a different property. A path which has just timed out is
    # still remembered as being in flight, so asking for it again would join the dead
    # request rather than make a new one - see the note in the test report.
    for path in ("target", "type"):
        with pytest.raises(EventProxyTimeout):
            await event_object.read(path)

    assert backend.disabled
    assert not backend.available
    with pytest.raises(EventProxyUnavailable):
        await event_object.read("key")


async def test_client_reported_timeouts_count_against_the_same_budget(monkeypatch):
    monkeypatch.setattr(REACTPY_EVENT_PROXY_MAX_TIMEOUTS, "current", 1)
    backend, _client = make_canned_client(
        ok=False, code="timeout", error="browser hung"
    )
    event_object = make_event(backend, "evt")

    with pytest.raises(EventProxyTimeout, match="did not answer"):
        await event_object.read("target")

    assert backend.disabled, "a timeout the client reports is still a timeout"


async def test_failures_the_client_cannot_explain_are_still_reported():
    backend, client = make_canned_client(ok=False)
    event_object = make_event(backend, "evt")

    with pytest.raises(EventProxyAccessError) as info:
        await event_object.read("target")

    assert "could not resolve ['target'] of event 'evt'" in str(info.value)
    assert "the client did not provide a reason" in str(info.value)
    assert not backend.disabled, "one refusal is not a broken connection"
    assert len(client.requests) == 1


async def test_a_failed_send_switches_live_access_off():
    backend = EventProxyBackend()
    sent: list[dict[str, Any]] = []

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)
        msg = "socket is closed"
        raise ConnectionResetError(msg)

    backend.set_sender(send)
    event_object = make_event(backend, "evt")

    with pytest.raises(EventProxyUnavailable, match="failed to send"):
        await event_object.read("target")

    assert len(sent) == 1, "the request was handed to the client once"
    assert backend.disabled
    assert not backend.available


async def test_a_call_made_from_another_thread_is_sent_by_the_loop():
    """A handler is free to think on a worker thread; the loop still does the sending

    Nothing about live access is thread safe - the connection to the browser belongs
    to the loop which accepted it - so a request conceived elsewhere is handed over
    rather than sent from the thread which thought of it.
    """
    backend, client = make_canned_client(ok=True)

    def call_from_a_worker() -> None:
        backend.notify("evt", ("log",), ["written"])

    await asyncio.to_thread(call_from_a_worker)
    await poll(lambda: client.sent)

    request = client.sent[0]
    assert request["type"] == EVENT_PROXY_REQUEST_TYPE
    assert request["path"] == ["log"]
    assert request["call"] is True
    assert request["args"] == ["written"]
    assert request["reply"] is False


async def test_closing_the_backend_fails_everything_still_in_flight():
    backend, client = make_client(make_objects(), respond=False)
    event_object = make_event(backend, "evt")
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


async def test_requests_made_just_after_the_loop_is_gone_fail_fast(monkeypatch):
    """A request which loses its loop on the way out is failed, not left waiting

    The connection to the browser belongs to the loop which accepted it. Once that
    loop has gone there is nothing left to send with, so whoever is waiting is failed
    rather than left holding a future nobody is ever going to answer.
    """
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")

    pending = asyncio.create_task(event_object.read("target"))
    # exactly one turn of the loop: the request is now queued, and the flush which
    # would carry it out has been scheduled behind this test rather than before it
    await asyncio.sleep(0)
    assert len(backend._outgoing) == 1
    monkeypatch.setattr(backend, "_loop", None)

    with pytest.raises(EventProxyUnavailable, match="no sender is bound"):
        await pending

    assert client.sent == [], "nothing was handed over a loop which no longer runs"


async def test_a_request_queued_while_the_loop_is_already_gone_is_never_sent(
    monkeypatch,
):
    """Nothing crosses the wire when there is no loop left to send it with

    The request is not handed to a loop which is gone, and the handler is not left
    waiting on a future forever either: the wait is bounded and ends as an
    ``EventProxyError``, whichever way the failure is reported.
    """
    monkeypatch.setattr(REACTPY_EVENT_PROXY_TIMEOUT, "current", 0.05)
    backend, client = make_client(make_objects())
    event_object = make_event(backend, "evt")
    monkeypatch.setattr(backend, "_loop", None)

    with pytest.raises(EventProxyError):
        await event_object.read("target")

    assert client.sent == []


# -- how event data is recognised and handed out -----------------------------


async def test_a_plain_string_marker_names_a_live_event_too():
    backend, client = make_client(make_objects())

    args = build_event_args(
        [{EVENT_MARKER_KEY: "evt", "type": "click"}, {"type": "click"}, "extra"],
        backend,
    )

    assert isinstance(args[0], Event)
    assert args[0].event_id == "evt"
    assert await args[0].type == "click"
    # data the client never marked was never a browser object, so it is handed over
    # exactly as it arrived rather than dressed up as a proxy nobody can resolve
    assert type(args[1]) is dict
    assert args[1] == {"type": "click"}
    assert args[2] == "extra"
    assert requested_paths(client) == [], "the type came free with the event"

    marked = build_event_args([{EVENT_MARKER_KEY: {"id": "evt"}}], backend)
    assert isinstance(marked[0], Event)
    assert marked[0].event_id == "evt"


async def test_only_what_the_client_volunteered_comes_free():
    """Only plain scalars travel with the event; everything else is read on demand"""
    backend, client = make_client(make_objects())
    (event_object,) = build_event_args(
        [
            {
                EVENT_MARKER_KEY: {"id": "evt"},
                "type": "click",
                "count": 3,
                "repeat": True,
                "target": {"value": "typed"},
                "nothing": None,
                "list": [1],
            }
        ],
        backend,
    )

    assert (await event_object.read("type", "count", "repeat")) == ("click", 3, True)
    assert requested_paths(client) == []
    for name in ("type", "count", "repeat"):
        assert name in dir(event_object)
    # an object which arrived alongside the id is not a value we may answer with
    assert "target" not in dir(event_object)
    assert await event_object.target.value == "typed"
    assert requested_paths(client) == [["target", "value"]]


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


async def test_layout_hands_data_which_is_not_a_browser_object_as_is():
    received: dict[str, Any] = {}

    async def on_click(event):
        received["event"] = event

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": on_click})

    _backend, client = make_client(make_objects())

    async with Layout(MyComponent()) as layout:
        connect(layout, client)
        model = (await layout.render())["model"]
        handlers = event_handlers_of(model)

        target = handlers["onClick"]["target"]
        data = {"type": "click", "detail": 3}
        await layout.deliver(event_message(target, data))
        await poll(lambda: "event" in received)

    # nothing marked this data as a live browser object, so it is passed straight on
    assert type(received["event"]) is dict
    assert received["event"] == {"type": "click", "detail": 3}
    assert EVENT_MARKER_KEY not in received["event"]
    assert client.requests == [], "nothing to reach into, so nothing was asked"


async def test_merged_handlers_all_share_the_same_event():
    """Merged handlers are handed the very same data, which each reads as it likes

    There is a single flavour of event data, so a merged handler never needs arguments
    dressed up differently from those of its siblings.
    """
    received: dict[str, Any] = {}

    async def first_handler(args):
        received["first"] = args[0]

    async def second_handler(args):
        received["second"] = args[0]

    merged = merge_event_handlers(
        [EventHandler(first_handler), EventHandler(second_handler)]
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

    assert isinstance(received["first"], Event)
    assert isinstance(received["second"], Event)
    assert received["first"] is received["second"]
    assert (await received["first"].read("type")) == ("click",)
    assert client.requests == [], "the type was already known to both of them"


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
    async def on_click(event):
        event.stopImmediatePropagation()

    @component
    def MyComponent():
        return reactpy.html.div({"onClick": on_click})

    async with Layout(MyComponent()) as layout:
        model = (await layout.render())["model"]
        handler = event_handlers_of(model)["onClick"]
        assert handler["stopPropagation"] is True
        assert handler["stopImmediatePropagation"] is True


async def test_a_timed_out_read_does_not_poison_that_path(monkeypatch):
    """A request which timed out must not be handed to whoever asks next

    The in-flight record used to be left behind when a read timed out, and the future
    inside it had already been cancelled by the wait. Reading the very same property
    again then took the "already in flight" branch and raised ``CancelledError`` at the
    handler rather than an :class:`EventProxyError` - and because that branch never
    reaches the timeout bookkeeping, the consecutive-timeout budget stopped counting,
    so a client stuck on one property could never trip the guard which switches live
    access off.
    """
    monkeypatch.setattr(REACTPY_EVENT_PROXY_TIMEOUT, "current", 0.05)
    monkeypatch.setattr(REACTPY_EVENT_PROXY_MAX_TIMEOUTS, "current", 3)
    backend, _client = make_client(make_objects(), respond=False)
    event_object = make_event(backend, "evt")

    for _ in range(3):
        with pytest.raises(EventProxyTimeout):
            await event_object.target.value

    # counting really happened, so the connection is now considered dead
    assert backend.disabled
    assert not backend.available
