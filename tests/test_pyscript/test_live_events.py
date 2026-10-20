"""Tests for the live event responder which the PyScript layout handler leans on.

:mod:`reactpy.executors.pyscript._live_events` is the reason ``await
event.target.value`` works in a page which has no server to ask. It is also the only
code in the PyScript executor holding on to browser objects, so what follows checks the
three things that make it safe and correct: a read reaches the object it names, a
blocked read is refused rather than quietly answered, and an object which has gone is
said to have gone.
"""

from __future__ import annotations

import sys
import types
from typing import Any

from reactpy._event_proxy import (
    EVENT_MARKER_KEY,
    EVENT_PROXY_REQUEST_TYPE,
    EVENT_REFERENCE_KEY,
)

# -- a stand-in for the page --------------------------------------------------
# This module normally talks to a browser through Pyodide's `js`. These tests run on
# CPython, so a small module stands in for it, and the fake objects below are shaped
# the way the browser shapes its own: what is on the instance is an own property and
# what is on the class is on the prototype, which is the distinction
# `collect_properties()` has to get right.


class _Undefined:
    def __repr__(self) -> str:  # pragma: no cover - only for a failing assertion
        return "undefined"


UNDEFINED = _Undefined()


class _FakeObject:
    def getOwnPropertyNames(self, value: Any) -> list[str]:
        if isinstance(value, type):
            return [name for name in vars(value) if not name.startswith("_")]
        return list(vars(value))

    def getPrototypeOf(self, value: Any) -> Any:
        if isinstance(value, type):
            chain = value.__mro__
            return chain[1] if len(chain) > 1 else None
        return type(value)


class _FakeArray:
    def isArray(self, value: Any) -> bool:
        return isinstance(value, list | tuple)


if "js" not in sys.modules:  # not running under Pyodide
    _js = types.ModuleType("js")
    _js.Object = _FakeObject()
    _js.Array = _FakeArray()
    _js.undefined = UNDEFINED
    sys.modules["js"] = _js

from reactpy.executors.pyscript._live_events import (  # noqa: E402
    LIVE_OBJECT_TTL_SECONDS,
    MAX_ALLOWED_DEPTH,
    MAX_CALL_RESULTS_PER_OBJECT,
    MAX_LIVE_OBJECTS,
    MAX_PROPERTIES,
    MAX_REQUESTS_PER_MESSAGE,
    EventProxyRegistry,
    InBrowserEventProxy,
    _allowed_depth,
    collect_properties,
    is_blocked_member,
    serialize_value,
)


class DomNode:
    """Members here belong to the prototype, the way a DOM object's do"""

    nodeType = 1
    tagName = "DIV"

    def focus(self) -> str:
        return "focused"


class FakeElement(DomNode):
    """An element: what a handler reads is on the instance"""

    tagName = "INPUT"

    def __init__(self, value: Any = None, checked: bool = False, **own: Any) -> None:
        self.value = value
        self.checked = checked
        self.__dict__.update(own)

    def adopt(self, other: Any) -> Any:
        """A method taking another live object as its argument"""
        return other.tagName

    def echo(self, *args: Any) -> list[Any]:
        """A method taking whatever the layout sent"""
        return list(args)


class FakeEvent(DomNode):
    def __init__(self, type: str = "change", target: Any = None, **own: Any) -> None:
        self.type = type
        self.target = target
        self.defaultPrevented = False
        self.cancelBubble = False
        self.__dict__.update(own)

    def preventDefault(self) -> None:
        self.defaultPrevented = True

    def stopPropagation(self) -> None:
        self.cancelBubble = True

    def composedPath(self) -> list[Any]:
        return [self.target]

    def callbacks(self) -> list[Any]:
        """A method whose answer holds something callable among the data"""
        return [self.noop, 1]

    def noop(self) -> None:
        pass


def request(event_id: str, *, path: list[str], call: bool = False, **extra: Any):
    return {
        "type": EVENT_PROXY_REQUEST_TYPE,
        "requestId": "req-0",
        "eventId": event_id,
        "path": path,
        "call": call,
        "args": [],
        "reply": True,
        "maxDepth": 16,
        **extra,
    }


# -- what may be read ---------------------------------------------------------


def test_blocked_members_match_the_browser_side():
    for name in ("ownerDocument", "document", "parentNode", "__proto__", "eval"):
        assert is_blocked_member(name), name
    for name in ("onclick", "onchange", "onerror"):
        assert is_blocked_member(name), name
    for name in ("value", "checked", "type", "tagName", "files", "key"):
        assert not is_blocked_member(name), name


def test_blocked_read_is_refused_rather_than_answered():
    proxy = InBrowserEventProxy()
    field = FakeElement(value="typed")
    event_id = proxy.registry.register(FakeEvent(target=field))

    for name, code in (
        ("ownerDocument", "access"),
        ("parentNode", "access"),
        ("nope", "not-found"),
    ):
        response = proxy.resolve(request(event_id, path=[name]))
        assert response["ok"] is False
        assert response["code"] == code


def test_read_reaches_the_object_the_event_came_from():
    proxy = InBrowserEventProxy()
    field = FakeElement(value="typed text")
    event_id = proxy.registry.register(FakeEvent(type="change", target=field))

    response = proxy.resolve(request(event_id, path=["target", "value"]))
    assert response["ok"] is True
    assert response["value"] == "typed text"


def test_property_from_the_prototype_is_readable_too():
    # Nearly everything interesting on a DOM object lives on its prototype, so a
    # snapshot built from own properties alone would be nearly empty.
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement()))

    tag = proxy.resolve(request(event_id, path=["target", "tagName"]))
    assert tag["value"] == "INPUT"
    assert proxy.resolve(request(event_id, path=["target", "nodeType"]))["value"] == 1


def test_a_method_is_pointed_at_and_then_called():
    proxy = InBrowserEventProxy()
    field = FakeElement()
    event_id = proxy.registry.register(FakeEvent(target=field))

    method = proxy.resolve(request(event_id, path=["target", "focus"]))
    assert method["value"][EVENT_REFERENCE_KEY]["callable"] is True

    called = proxy.resolve(request(event_id, path=["target", "focus"], call=True))
    assert called["ok"] is True
    assert called["value"] == "focused"


def test_a_path_leads_through_what_a_call_answered():
    # The layout is handed the list composedPath() returned and then asks for a member
    # of it; reaching that member means answering the call once and walking the result,
    # not calling the method a second time.
    proxy = InBrowserEventProxy()
    field = FakeElement(value="typed text")
    event_id = proxy.registry.register(FakeEvent(target=field))

    assert proxy.resolve(
        request(event_id, path=["composedPath"], call=True)
    )["ok"] is True
    response = proxy.resolve(request(event_id, path=["composedPath", "0", "value"]))
    assert response["ok"] is True, response
    assert response["value"] == "typed text"


def test_calling_a_blocked_member_is_refused():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement()))
    response = proxy.resolve(request(event_id, path=["eval"], call=True))
    assert response["ok"] is False and response["code"] == "access"


# -- what comes back ----------------------------------------------------------


def test_a_snapshot_leaves_methods_out_and_carries_data():
    properties = collect_properties(FakeEvent(type="change", target=FakeElement("x")))
    assert properties["type"] == "change"
    assert properties["nodeType"] == 1  # from the prototype
    assert "focus" not in properties and "preventDefault" not in properties


def test_a_value_too_deep_comes_back_as_a_reference():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement(value="x")))
    shallow = proxy.resolve(request(event_id, path=["target"], maxDepth=0))
    assert shallow["value"][EVENT_REFERENCE_KEY]["path"] == ["target"]


def test_a_long_list_is_cut_short_and_pointed_at():
    event_id = "evt"
    items = list(range(MAX_PROPERTIES + 5))
    serialized = serialize_value(items, event_id)
    assert len(serialized) == MAX_PROPERTIES + 1
    assert serialized[-1][EVENT_REFERENCE_KEY]["path"] == []


def test_a_cycle_comes_back_as_a_reference_rather_than_recursion():
    event = FakeEvent(type="change")
    event.currentTarget = event
    serialized = serialize_value(event, "evt")
    # pointed at from where the walk stood, rather than expanded a second time
    assert serialized["currentTarget"][EVENT_REFERENCE_KEY]["path"] == ["currentTarget"]


# -- what goes away -----------------------------------------------------------


def test_an_unknown_id_says_nothing_is_registered():
    proxy = InBrowserEventProxy()
    response = proxy.resolve(request("missing", path=["value"]))
    assert response["ok"] is False and response["code"] == "not-found"


def test_an_id_dropped_to_make_room_says_so():
    registry = EventProxyRegistry()
    starved = registry.register(FakeEvent())  # never read, so it goes first
    for _ in range(MAX_LIVE_OBJECTS):
        reader = registry.register(FakeEvent())
        assert registry.get(reader) is not None  # keep it, prove it is wanted
    registry.prune()

    error, code = registry.missing(starved)
    assert code == "evicted"
    assert "no longer fits" in error

    assert registry.size == MAX_LIVE_OBJECTS


async def test_the_object_still_being_read_is_never_the_one_dropped():
    # What goes when the page runs out of room is whatever has gone longest without a
    # read, so a handler part way through awaiting something cannot have the object
    # yanked out from under it by traffic which has nothing to do with it.
    proxy = InBrowserEventProxy()
    in_flight = proxy.registry.register(FakeEvent(type="change"))
    quiet = [proxy.registry.register(FakeEvent()) for _ in range(MAX_LIVE_OBJECTS - 1)]

    for _ in range(20):
        await proxy.send(request(in_flight, path=["target", "value"]))

    for _ in range(10):
        proxy.registry.register(FakeEvent())

    assert proxy.registry.get(in_flight) is not None
    assert proxy.registry.missing(quiet[0])[1] == "evicted"


# -- dispatching --------------------------------------------------------------


def test_a_dispatched_event_carries_an_id_and_nothing_else():
    proxy = InBrowserEventProxy()
    field = FakeElement(value="typed text")

    (data,) = proxy.event_data((FakeEvent(type="change", target=field),), {})

    assert set(data) == {EVENT_MARKER_KEY, "type"}
    assert data["type"] == "change"
    event_id = data[EVENT_MARKER_KEY]["id"]
    assert proxy.registry.get(event_id).value.target is field
    # the object itself did not travel, so a handler cannot be handed a raw page object
    assert "target" not in data


def test_a_dispatched_event_honours_what_the_element_asked_for():
    proxy = InBrowserEventProxy()
    event = FakeEvent(type="submit")

    proxy.event_data((event,), {"preventDefault": True, "stopPropagation": True})
    assert event.defaultPrevented and event.cancelBubble

    other = FakeEvent(type="click")
    proxy.event_data((other,), {})
    assert not other.defaultPrevented


def test_a_scalar_argument_survives_the_trip():
    proxy = InBrowserEventProxy()
    data = proxy.event_data((FakeEvent(), 3, "hello"), {})
    assert data[1:] == [3, "hello"]


async def test_batched_requests_are_answered_together():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement(value="v")))

    replies: list[dict[str, Any]] = []
    proxy._deliver = replies.append
    await proxy.send(
        {
            "type": EVENT_PROXY_REQUEST_TYPE,
            "requests": [
                request(event_id, path=["type"]) | {"requestId": "a"},
                request(event_id, path=["target", "value"]) | {"requestId": "b"},
                request(event_id, path=["target"])
                | {"requestId": "c", "reply": False},
            ],
        }
    )

    assert len(replies) == 1
    answers = {r["requestId"]: r for r in replies[0]["responses"]}
    assert answers["a"]["value"] == "change"
    assert answers["b"]["value"] == "v"
    assert "c" not in answers


async def test_a_request_which_is_not_one_of_ours_is_ignored():
    proxy = InBrowserEventProxy()
    await proxy.send({"type": "layout-update"})
    await proxy.send({})


# -- the finer points ---------------------------------------------------------------


def test_the_markers_themselves_and_the_dunder_namespace_are_blocked():
    assert is_blocked_member(EVENT_MARKER_KEY)
    assert is_blocked_member(EVENT_REFERENCE_KEY)
    assert is_blocked_member("__dict__")
    assert not is_blocked_member("on")  # too short to be an attribute name
    assert not is_blocked_member("value")


def test_a_string_can_be_measured_and_indexed():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement(value="abc")))

    for path, expected in (
        (["target", "value", "length"], 3),
        (["target", "value", "1"], "b"),
        (["target", "value", "9"], None),  # past the end, as it would be on the page
    ):
        response = proxy.resolve(request(event_id, path=path))
        assert response["value"] == expected, path
    assert (
        proxy.resolve(request(event_id, path=["target", "value", "nope"]))["code"]
        == "not-found"
    )


def test_a_primitive_has_nothing_to_read_off_it():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent())
    response = proxy.resolve(request(event_id, path=["nodeType", "anything"]))
    assert response["ok"] is False and response["code"] == "not-found"


def test_a_number_names_an_element_rather_than_an_attribute():
    # "0" is an index wherever one exists, and merely a missing property where one does
    # not - the same answer either way, reached a different way
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement(value="v")))
    assert proxy.resolve(request(event_id, path=["target", "0"]))["code"] == "not-found"

    proxy.resolve(request(event_id, path=["composedPath"], call=True))
    gone = proxy.resolve(request(event_id, path=["composedPath", "7"]))
    assert gone["code"] == "not-found"


# -- what comes back, when it is awkward ------------------------------------------------


def test_a_member_which_throws_on_being_read_is_simply_left_out():
    class WithABrokenGetter(FakeElement):
        @property
        def exploding(self) -> None:
            msg = "this getter has opinions"
            raise RuntimeError(msg)

    properties = collect_properties(WithABrokenGetter(value="v"))
    assert "exploding" not in properties
    assert properties["value"] == "v"


def test_a_snapshot_stops_counting_at_the_limit():
    crowded = FakeElement(**{f"extra{n}": n for n in range(MAX_PROPERTIES + 5)})
    assert len(collect_properties(crowded, max_properties=6)) == 6


def test_values_come_back_in_the_shape_a_handler_can_use():
    import datetime as dt

    event = FakeEvent(
        type="click",
        when=dt.datetime(2024, 5, 2, 12, 30, tzinfo=dt.UTC),
        day=dt.date(2024, 5, 2),
        ratio=float("nan"),
        huge=float("inf"),
        blob=b"not something a page can hand over",
    )
    serialized = serialize_value(event, "evt")
    assert serialized["when"] == "2024-05-02T12:30:00+00:00"
    assert serialized["day"] == "2024-05-02"
    assert serialized["ratio"] is None
    assert serialized["huge"] is None
    assert serialized["blob"] is None


def test_a_list_which_cannot_be_measured_comes_back_without_items():
    class Unmeasurable:
        def __iter__(self):
            return iter([1, 2, 3])

    def is_array(value: Any) -> bool:
        if isinstance(value, Unmeasurable):
            return True
        msg = "not a value JavaScript has an opinion about"
        raise RuntimeError(msg)

    original = _js.Array.isArray
    _js.Array.isArray = is_array
    try:
        # no length to go by, so nothing is claimed; and a value the page will not
        # classify is still answered for, out of whatever it can walk
        assert serialize_value(Unmeasurable(), "evt") == []
        assert serialize_value([1, 2], "evt") == [1, 2]
    finally:
        _js.Array.isArray = original


def test_an_iterable_comes_back_as_a_list_and_is_cut_short():
    class NodeList:
        def __iter__(self):
            return iter(range(MAX_PROPERTIES + 5))

    serialized = serialize_value(NodeList(), "evt")
    assert len(serialized) == MAX_PROPERTIES + 1
    assert serialized[0] == 0
    assert serialized[-1][EVENT_REFERENCE_KEY]["path"] == []


def test_a_chain_which_cannot_be_walked_is_simply_a_shorter_chain():
    original = _js.Object.getPrototypeOf
    for substitute in (_raise, lambda value: UNDEFINED):
        _js.Object.getPrototypeOf = substitute
        try:
            assert collect_properties(FakeElement(value="v"))["value"] == "v"
            assert "nodeType" not in collect_properties(FakeElement(value="v"))
        finally:
            _js.Object.getPrototypeOf = original


# -- what goes away, when it is awkward -------------------------------------------------


def test_only_so_many_call_results_are_kept_per_object():
    registry = EventProxyRegistry()
    entry = registry.get(registry.register(FakeEvent()))
    total = MAX_CALL_RESULTS_PER_OBJECT + 4
    for index in range(total):
        entry.remember_call([f"method{index}"], FakeElement(value=str(index)))
        entry.remember_call([f"primitive{index}"], "nothing to walk into")

    assert len(entry.calls) == MAX_CALL_RESULTS_PER_OBJECT
    # a primitive has nothing inside it, and the oldest answers made room for the newest
    assert entry.answer_for([f"method{total - 1}"]).value == str(total - 1)
    assert entry.answer_for(["method0"]) == entry.answer_for(["nothing-was-stored"])


def test_an_id_nobody_ever_read_is_forgotten_once_it_is_stale():
    now = [1000.0]
    registry = EventProxyRegistry(clock=lambda: now[0])
    stale = registry.register(FakeEvent())
    wanted = registry.register(FakeEvent())
    registry.get(wanted)  # the layout read it once, so age does not apply to it

    now[0] += LIVE_OBJECT_TTL_SECONDS + 1
    registry.prune()

    assert registry.get(stale) is None
    assert registry.missing(stale)[1] == "not-found"  # stale, not squeezed out
    assert registry.get(wanted) is not None


def test_the_reason_an_id_went_missing_is_not_kept_forever():
    registry = EventProxyRegistry()
    first = registry.register(FakeEvent())
    for _ in range(2 * MAX_LIVE_OBJECTS):
        registry.register(FakeEvent())

    assert registry.size == MAX_LIVE_OBJECTS
    # the record of why is bounded too, so the very first reason has aged out of it
    assert registry.missing(first)[1] == "not-found"


# -- answering, when the request is not what was expected -------------------------------


async def test_a_batch_carrying_too_many_requests_refuses_the_excess():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(type="change"))

    replies: list[dict[str, Any]] = []
    proxy._deliver = replies.append
    await proxy.send(
        {
            "type": EVENT_PROXY_REQUEST_TYPE,
            "requests": [
                request(event_id, path=["type"]) | {"requestId": str(index)}
                for index in range(MAX_REQUESTS_PER_MESSAGE + 2)
            ],
        }
    )

    answers = replies[0]["responses"]
    assert len(answers) == MAX_REQUESTS_PER_MESSAGE + 2
    assert answers[MAX_REQUESTS_PER_MESSAGE]["ok"] is False
    assert "may not ask for more than" in answers[-1]["error"]


async def test_a_request_answered_without_anywhere_to_send_it_is_harmless():
    proxy = InBrowserEventProxy()  # never bound to a layout
    await proxy.send(request("missing", path=["value"]))


async def test_calling_something_which_is_not_a_function_is_refused():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement(value="v")))

    no_path = proxy.resolve(request(event_id, path=[], call=True))
    assert no_path["ok"] is False and "cannot be called" in no_path["error"]

    not_a_method = proxy.resolve(request(event_id, path=["target", "value"], call=True))
    assert not_a_method["ok"] is False and "not a function" in not_a_method["error"]


async def test_an_argument_naming_another_live_object_is_handed_over():
    proxy = InBrowserEventProxy()
    adopting = proxy.registry.register(FakeEvent(target=FakeElement(tagName="SECTION")))
    adopted = proxy.registry.register(FakeEvent(target=FakeElement()))

    response = proxy.resolve(
        request(
            adopting,
            path=["target", "adopt"],
            call=True,
            args=[{EVENT_REFERENCE_KEY: {"eventId": adopted, "path": ["target"]}}],
        )
    )
    assert response["ok"] is True, response
    assert response["value"] == "INPUT"


async def test_an_argument_naming_a_gone_object_says_why():
    proxy = InBrowserEventProxy()
    caller = proxy.registry.register(FakeEvent(target=FakeElement()))

    gone = proxy.resolve(
        request(
            caller,
            path=["target", "adopt"],
            call=True,
            args=[{EVENT_REFERENCE_KEY: {"eventId": "never-seen", "path": []}}],
        )
    )
    assert gone["code"] == "not-found"

    # the page runs out of room, and what goes is whatever went longest without a read
    squeezed = proxy.registry.register(FakeEvent(target=FakeElement()))
    proxy.registry.get(caller)
    for _ in range(MAX_LIVE_OBJECTS):
        extra = proxy.registry.register(FakeEvent())
        proxy.registry.get(extra)

    assert proxy.registry.get(squeezed) is None
    evicted = proxy.resolve(
        request(
            caller,
            path=["target", "adopt"],
            call=True,
            args=[{EVENT_REFERENCE_KEY: {"eventId": squeezed, "path": []}}],
        )
    )
    assert evicted["code"] == "evicted"


async def test_an_argument_nested_past_the_bound_is_refused():
    proxy = InBrowserEventProxy()
    caller = proxy.registry.register(FakeEvent(target=FakeElement()))
    response = proxy.resolve(
        request(
            caller,
            path=["target", "adopt"],
            call=True,
            args=[[[1, 2]]],
            maxDepth=1,
        )
    )
    assert response["ok"] is False and "nested more deeply" in response["error"]


def test_a_flag_the_page_cannot_honour_is_said_rather_than_raised():
    class EventWithoutFlags:
        type = "submit"

    proxy = InBrowserEventProxy()
    data = proxy.event_data((EventWithoutFlags(),), {"preventDefault": True})
    assert EVENT_MARKER_KEY in data[0]


def test_an_event_type_which_cannot_be_read_is_left_out():
    class Unreadable:
        @property
        def type(self) -> int:
            msg = "the page would not say"
            raise RuntimeError(msg)

    class Numeric:
        type = 7

    proxy = InBrowserEventProxy()
    # the type is the one thing sent up front, and only when it is actually a string
    assert "type" not in proxy.event_data((Unreadable(),), {})[0]
    assert "type" not in proxy.event_data((Numeric(),), {})[0]


def test_the_depth_a_request_asks_for_is_read_sensibly():
    for proposed, expected in (
        (None, 0),
        ("deep", 0),
        (True, 0),
        (-1, 0),
        (float("nan"), 0),
        (float("inf"), 0),
        (4, 4),
        (10**9, MAX_ALLOWED_DEPTH),
    ):
        assert _allowed_depth(proposed) == expected, proposed


# -- answering the shapes a page can hand over ------------------------------------------


async def test_a_read_of_the_whole_object_describes_it():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(
        FakeEvent(type="change", target=FakeElement(value="v"))
    )
    response = proxy.resolve(request(event_id, path=[]))
    assert response["ok"] is True, response
    assert response["value"]["type"] == "change"
    assert response["value"]["target"]["value"] == "v"


async def test_something_callable_in_a_collection_is_pointed_at():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent())
    response = proxy.resolve(request(event_id, path=["callbacks"], call=True))
    assert response["value"][0][EVENT_REFERENCE_KEY]["callable"] is True
    assert response["value"][1] == 1


async def test_plain_data_arguments_are_handed_over_as_they_arrive():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(target=FakeElement()))
    response = proxy.resolve(
        request(
            event_id,
            path=["target", "echo"],
            call=True,
            args=[{"note": "not a reference"}, 7, [1, "x"], True],
        )
    )
    assert response["ok"] is True, response
    assert response["value"] == [{"note": "not a reference"}, 7, [1, "x"], True]


async def test_a_batch_carrying_something_that_is_not_a_request_skips_it():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(type="change"))

    replies: list[dict[str, Any]] = []
    proxy._deliver = replies.append
    await proxy.send(
        {
            "type": EVENT_PROXY_REQUEST_TYPE,
            "requests": [
                None,
                "not a request",
                request(event_id, path=["type"]) | {"requestId": "real"},
            ],
        }
    )

    assert len(replies) == 1
    assert len(replies[0]["responses"]) == 1
    assert replies[0]["responses"][0]["value"] == "change"


async def test_a_page_which_cannot_be_described_is_answered_as_denied():
    proxy = InBrowserEventProxy()
    event_id = proxy.registry.register(FakeEvent(type="change"))

    original = _js.Object.getOwnPropertyNames
    _js.Object.getOwnPropertyNames = _raise
    try:
        response = proxy.resolve(request(event_id, path=[]))
    finally:
        _js.Object.getOwnPropertyNames = original

    assert response["ok"] is False
    assert response["code"] == "access"


def _raise(value: Any) -> None:
    msg = "the page refused"
    raise RuntimeError(msg)


# -- the layout's own path ----------------------------------------------------


async def test_a_handler_reading_the_event_gets_the_answer():
    """The end of the road: a handler awaiting a property gets it, and the page updates"""
    from reactpy import component, html, use_state
    from reactpy.core.layout import Layout

    reads: list[Any] = []

    @component
    def Demo():
        state, set_state = use_state("")

        async def on_change(event):
            reads.append(await event.target.value)
            set_state(reads[-1])

        return html.input({"value": state, "onChange": on_change})

    layout = Layout(Demo())
    proxy = InBrowserEventProxy()

    async with layout:
        proxy.bind(layout)
        layout.set_event_proxy_sender(proxy.send)
        model = (await layout.render())["model"]

        field = FakeElement(value="typed text")
        await layout.deliver(
            {
                "type": "layout-event",
                "target": _find_handler_target(model),
                "data": proxy.event_data((FakeEvent(type="change", target=field),), {}),
            }
        )
        update = await layout.render()

    assert reads == ["typed text"]
    assert "typed text" in str(update["model"])


async def test_a_handler_reading_something_blocked_is_told_so():
    from reactpy import component, html, use_state
    from reactpy._event_proxy import EventProxyAccessError
    from reactpy.core.layout import Layout

    caught: list[BaseException] = []

    @component
    def Demo():
        state, set_state = use_state("idle")

        async def on_click(event):
            try:
                await event.target.ownerDocument.title
            except Exception as error:  # recorded, not swallowed
                caught.append(error)
            set_state("done")

        return html.button({"onClick": on_click, "children": state})

    layout = Layout(Demo())
    proxy = InBrowserEventProxy()

    async with layout:
        proxy.bind(layout)
        layout.set_event_proxy_sender(proxy.send)
        model = (await layout.render())["model"]

        await layout.deliver(
            {
                "type": "layout-event",
                "target": _find_handler_target(model),
                "data": proxy.event_data((FakeEvent(type="click"),), {}),
            }
        )
        update = await layout.render()

    assert len(caught) == 1
    assert isinstance(caught[0], EventProxyAccessError)
    assert "done" in str(update["model"])


def _find_handler_target(node: Any) -> str:
    if isinstance(node, dict):
        handlers = node.get("eventHandlers")
        if isinstance(handlers, dict) and handlers:
            return next(iter(handlers.values()))["target"]
        for value in node.values():
            found = _find_handler_target(value)
            if found:
                return found
    elif isinstance(node, list | tuple):
        for value in node:
            found = _find_handler_target(value)
            if found:
                return found
    return ""
