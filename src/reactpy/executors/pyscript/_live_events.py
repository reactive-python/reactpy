"""Answers live event reads for a layout which runs *inside* the browser.

Ordinary ReactPy runs the layout on the server, so a handler which reads
``await event.target.value`` has to ask the page over a connection. The PyScript executor
is different: the layout and the page are in the same interpreter, so there is no
connection to ask - but the handler is the same code either way, and it still says
``await``.

Something therefore has to play the part of the browser for that layout, and this module
is that something. When an element is given a handler, the object the browser hands over
is registered here under an id and the event is dispatched as a marker naming it::

    {"__reactpy_event__": {"id": "..."}, "type": "change"}

which is exactly what a server side client sends, so :class:`~reactpy.types.Event` is
built identically and a handler cannot tell the two apart. Reads then arrive back here as
``event-proxy-request`` messages and are answered against the object itself, under the
same rules :file:`event-proxy.ts` sets: a blocked member is refused rather than answered
with :data:`None`, a method is called and its result kept so a path leading through one
still resolves, and whatever will not fit is handed back as a reference to be asked about
on its own.

Keeping those objects is what makes any of this work, and it is also the only thing here
which can grow without bound, so the registry is capped and swept the way the client's
is. An object which goes away while a handler is still reading it is the failure worth
naming precisely, which is why ``evicted`` and ``not-found`` are kept apart.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
from collections import OrderedDict
from collections.abc import Mapping
from time import monotonic
from typing import Any
from uuid import uuid4

import js

from reactpy._event_proxy import (
    EVENT_MARKER_KEY,
    EVENT_PROXY_REQUEST_TYPE,
    EVENT_PROXY_RESPONSE_TYPE,
    EVENT_REFERENCE_KEY,
)

logger = logging.getLogger(__name__)

MAX_LIVE_OBJECTS = 512
"""How many dispatched objects are kept at most - see ``MAX_LIVE_OBJECTS`` in the client"""

LIVE_OBJECT_TTL_SECONDS = 60.0
"""How long an object the layout never once asked about may sit unused"""

MAX_PROPERTIES = 100
"""How many members of one object, list, or iterable are handed over at most"""

MAX_ALLOWED_DEPTH = 128
"""The deepest a request may ask this side to go, however it asks"""

MAX_REQUESTS_PER_MESSAGE = 256
"""How many requests one batched message may carry out"""

MAX_CALL_RESULTS_PER_OBJECT = 16
"""How many call results one object keeps around in order to walk paths through them"""

#: What must never leave the page. This is a security control rather than a size one:
#: with nothing sent up front, it is the only thing standing between a request and the
#: rest of the browser. It is kept in step with ``BLOCKED_MEMBERS`` in
#: :file:`event-proxy.ts` on purpose - the same read should work, or be refused, in both
#: places, because a handler cannot tell which one it is running in.
BLOCKED_MEMBERS = frozenset(
    {
        # reaching the rest of the document, or the browser itself
        "ownerDocument",
        "document",
        "defaultView",
        "parentWindow",
        "ownerWindow",
        "window",
        "globalThis",
        "self",
        "top",
        "frames",
        "contentWindow",
        "contentDocument",
        "navigator",
        "location",
        "localStorage",
        "sessionStorage",
        "cookie",
        # reaching style sheets, which can carry same origin URLs
        "ownerNode",
        "sheets",
        "styleSheet",
        # tree traversal - walk composedPath() or the snapshot instead
        "parentNode",
        "parentElement",
        "childNodes",
        "firstChild",
        "lastChild",
        "nextSibling",
        "previousSibling",
        "firstElementChild",
        "lastElementChild",
        "nextElementSibling",
        "previousElementSibling",
        "children",
        "assignedSlot",
        "shadowRoot",
        "host",
        # prototype and realm access
        "__proto__",
        "constructor",
        "prototype",
        "eval",
        "execScript",
        "Function",
        "setTimeout",
        "setInterval",
        "import",
    }
)


class ProxyError(Exception):
    """Something went wrong while answering a live event read"""

    code = "access"


class ProxyNotFoundError(ProxyError):
    """The object, or the property on it, is not there"""

    code = "not-found"


class ProxyEvictedError(ProxyNotFoundError):
    """The object was dropped to make room while the layout was still reading it"""

    code = "evicted"


class ProxyAccessError(ProxyError):
    """The page refused the read outright"""

    code = "access"


_EVENT_ATTRIBUTE_PREFIX = "on"


def is_blocked_member(name: str) -> bool:
    """Whether ``name`` must not be read from a live object"""
    if name in BLOCKED_MEMBERS:
        return True
    if name in {EVENT_MARKER_KEY, EVENT_REFERENCE_KEY}:
        return True
    # event handler attributes (``onclick``, ``onerror``, ...) are functions, and the
    # double underscore namespace belongs to whoever built the page
    prefix = len(_EVENT_ATTRIBUTE_PREFIX)
    is_handler_attribute = (
        len(name) > prefix
        and name[:prefix].lower() == _EVENT_ATTRIBUTE_PREFIX
        and name[prefix].isalpha()
    )
    if is_handler_attribute:
        return True
    return name.startswith("__") and name.endswith("__")


# -- reflection -------------------------------------------------------------
# Everything here reaches into a browser object the only way Pyodide allows.


def _undefined() -> Any:
    return getattr(js, "undefined", None)


def _is_js_object(value: Any) -> bool:
    """Whether ``value`` is something the page would call an object or a function"""
    return value is not None and value is not _undefined() and not isinstance(
        value, str | bytes | bytearray | int | float | bool | dt.date
    )


def _is_array(value: Any) -> bool:
    try:
        return bool(js.Array.isArray(value))
    except Exception:  # not a value JavaScript has an opinion about
        return False


def _is_iterable(value: Any) -> bool:
    return hasattr(value, "__iter__")


def _own_names(value: Any) -> list[str]:
    """Every readable name on ``value`` itself, including accessor properties"""
    return [str(name) for name in js.Object.getOwnPropertyNames(value)]


def _prototype_of(value: Any) -> Any:
    try:
        prototype = js.Object.getPrototypeOf(value)
    except Exception:
        return None
    if prototype is None or prototype is _undefined():
        return None
    return prototype


def _read(node: Any, name: str) -> Any:
    """Read one property off a live object, or say why it could not be read"""
    if node is None or node is _undefined():
        msg = f'cannot read "{name}" of nothing'
        raise ProxyNotFoundError(msg)
    if isinstance(node, str):
        if name == "length":
            return len(node)
        if name.isdigit():
            index = int(name)
            return node[index] if index < len(node) else None
        msg = f'cannot read "{name}" of a string'
        raise ProxyNotFoundError(msg)
    if isinstance(node, bool | int | float):
        msg = f'cannot read "{name}" of a primitive'
        raise ProxyNotFoundError(msg)
    if name.isdigit():
        # A list or a NodeList is addressed by index, and a numeric path segment has to
        # reach an element the same way `arr[0]` would on the page.
        try:
            return node[int(name)]
        except (TypeError, IndexError, KeyError):
            pass
    try:
        return getattr(node, name)
    except AttributeError as error:
        msg = f'"{name}" does not exist'
        raise ProxyNotFoundError(msg) from error
    except Exception as error:  # getters throw (detached nodes, ...)
        msg = f'reading "{name}" failed: {error}'
        raise ProxyAccessError(msg) from error


def read_property(node: Any, name: str) -> Any:
    """Read a single property of a live object, refusing anything blocked"""
    if is_blocked_member(name):
        msg = f'reading "{name}" is not allowed'
        raise ProxyAccessError(msg)
    return _read(node, name)


def collect_properties(value: Any, max_properties: int = MAX_PROPERTIES) -> dict:
    """The readable, non-function members of ``value``, prototype chain included

    Own properties are not enough for a DOM object - nearly everything interesting lives
    on its prototype - so the chain is walked the way a property read on the page would
    resolve it. Blocked names never make it into the result, and neither do methods:
    those are called by an explicit path, not handed over as data.
    """
    collected: dict[str, Any] = {}
    count = 0
    prototype: Any = value
    while prototype is not None and count < max_properties:
        for name in _own_names(prototype):
            if name in collected or is_blocked_member(name):
                continue
            try:
                property_value = _read(value, name)
            except ProxyError:
                continue  # a getter which throws is simply not readable
            if callable(property_value):
                continue  # methods are called, not sent
            collected[name] = property_value
            count += 1
            if count >= max_properties:
                break
        prototype = _prototype_of(prototype)
    return collected


def _reference(event_id: str, path: list[str], callable_: bool = False) -> dict:
    """Build the marker the layout turns back into a proxy"""
    value: dict[str, Any] = {"eventId": event_id, "path": path}
    if callable_:
        value["callable"] = True
    return {EVENT_REFERENCE_KEY: value}


def serialize_value(
    value: Any,
    event_id: str,
    *,
    path: list[str] | None = None,
    max_depth: int = MAX_ALLOWED_DEPTH,
    depth: int = 0,
    seen: set[int] | None = None,
) -> Any:
    """Turn a live browser value into the answer to one on-demand read

    Anything too deep, too large, recursive, or simply not data is replaced with a
    reference, which is what lets a handler reach further down one property at a time
    rather than in one enormous answer.
    """
    path = [] if path is None else path
    seen = set() if seen is None else seen

    if value is None or value is _undefined():
        return None
    if isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()

    if callable(value) and not isinstance(value, type):
        return _reference(event_id, path, True)
    if not _is_js_object(value):
        return None

    if id(value) in seen:
        # A cycle, or one node shared between two properties: better pointed at than
        # expanded a second time.
        return _reference(event_id, path)
    if depth >= max_depth:
        return _reference(event_id, path)
    seen.add(id(value))

    def step(item: Any, segment: str) -> Any:
        return serialize_value(
            item,
            event_id,
            path=[*path, segment],
            max_depth=max_depth,
            depth=depth + 1,
            seen=seen,
        )

    if isinstance(value, Mapping):
        # A plain set of named members, which is how the page describes anything which
        # is not a list - and the reason this comes first: a mapping is iterable over
        # its keys, which is the last thing its answer should be made of.
        return {str(name): step(item, str(name)) for name, item in value.items()}

    if _is_array(value):
        # A list is a collection of members like any other, so it is bounded the same
        # way. What did not fit is pointed at rather than dropped without a trace, which
        # leaves the layout free to walk the rest one index at a time.
        try:
            length = len(value)
        except Exception:
            length = 0
        items = [
            step(value[index], str(index))
            for index in range(min(length, MAX_PROPERTIES))
        ]
        if length > len(items):
            items.append(_reference(event_id, path))
        return items

    if _is_iterable(value):
        # NodeList, FileList, Set, Map, ... all read better as a list
        items = []
        for index, item in enumerate(value):
            if index >= MAX_PROPERTIES:
                items.append(_reference(event_id, path))
                break
            items.append(step(item, str(index)))
        return items

    return {name: step(item, name) for name, item in collect_properties(value).items()}


def _call_key(path: list[str]) -> str:
    """What a recorded call is filed under - its own path, and nothing else's"""
    return json.dumps(path)


class LiveObject:
    """A dispatched browser object, plus what has been read out of it since"""

    __slots__ = ("added", "asked", "calls", "value")

    def __init__(self, value: Any, added: float) -> None:
        self.value = value
        self.added = added
        self.asked = False
        self.calls: OrderedDict[str, Any] = OrderedDict()

    def remember_call(self, path: list[str], result: Any) -> None:
        """Keep what a call answered, so that a path through it still resolves"""
        if result is None or isinstance(result, str | bytes | bool | int | float):
            return  # a primitive has nothing inside it to walk into
        self.calls[_call_key(path)] = result
        while len(self.calls) > MAX_CALL_RESULTS_PER_OBJECT:
            self.calls.popitem(last=False)

    def answer_for(self, path: list[str]) -> Any:
        """What this object's own ``path`` previously answered, if it ever did"""
        return self.calls.get(_call_key(path), _MISSING)


_MISSING = object()


def _step_down(entry: LiveObject, node: Any, path: list[str], index: int) -> Any:
    """One segment deeper, through what a method answered rather than the method

    The reference the layout is holding came out of that answer, and asking the method
    again would be both a second side effect and a different answer.
    """
    if callable(node) and not isinstance(node, type):
        answer = entry.answer_for(path[:index])
        if answer is not _MISSING:
            node = answer
    return read_property(node, path[index])


def read_path(entry: LiveObject, path: list[str]) -> Any:
    """Follow a whole property path against a live object, refusing blocked names"""
    node = entry.value
    for index in range(len(path)):
        node = _step_down(entry, node, path, index)
    return node


class EventProxyRegistry:
    """The objects which recently triggered an event, kept for the layout to walk

    This is the only place those objects exist as far as the layout is concerned: nothing
    about them travels with the event, so forgetting one is not a slowdown but a dead end.
    """

    def __init__(self, clock: Any = None) -> None:
        self._clock = monotonic if clock is None else clock
        self._live: OrderedDict[str, LiveObject] = OrderedDict()
        self._dropped: OrderedDict[str, str] = OrderedDict()

    @property
    def size(self) -> int:
        return len(self._live)

    def register(self, value: Any) -> str:
        """Take the object a dispatched event arrived with, and name it"""
        event_id = uuid4().hex
        self._live[event_id] = LiveObject(value, self._clock())
        self.prune()
        return event_id

    def get(self, event_id: str) -> LiveObject | None:
        """The object behind ``event_id``, marked as used right now

        Marking it is what makes the cap a least-recently-used bound rather than a queue:
        without it an object could be dropped while a handler was part way through
        reading it, purely because it happened to have been dispatched early.
        """
        entry = self._live.get(event_id)
        if entry is None:
            return None
        entry.asked = True
        entry.added = self._clock()
        self._live.move_to_end(event_id)
        return entry

    def prune(self) -> None:
        """Let go of what nobody wanted, then make room if there is not enough

        Two rules, each with one job. Age takes what was dispatched, never once read, and
        is only taking up room; it deliberately leaves alone an object the layout *has*
        read, because the handler which read it may simply be part way through awaiting
        something slow. Count is what actually bounds the page, and it takes whatever has
        gone longest without a read.
        """
        now = self._clock()
        for event_id in [
            event_id
            for event_id, entry in self._live.items()
            if not entry.asked and now - entry.added > LIVE_OBJECT_TTL_SECONDS
        ]:
            del self._live[event_id]
            self._note(event_id, "expired")
        while len(self._live) > MAX_LIVE_OBJECTS:
            evicted = next(iter(self._live))
            del self._live[evicted]
            self._note(evicted, "evicted")

    def _note(self, event_id: str, reason: str) -> None:
        """Remember why an id stopped answering, for as long as there is room to"""
        self._dropped.pop(event_id, None)
        self._dropped[event_id] = reason
        while len(self._dropped) > MAX_LIVE_OBJECTS:
            self._dropped.popitem(last=False)

    def missing(self, event_id: str) -> tuple[str, str]:
        """Say why an id is not answering, in a way the layout can tell apart

        ``evicted`` is the one worth a look at the page rather than at the handler: the
        registry ran out of room under a layout which was still reading. Everything else -
        never registered, or idle and never once read - is the ordinary ``not-found``.
        """
        if self._dropped.get(event_id) == "evicted":
            return (
                f"event {event_id!r} no longer fits - this page keeps at most "
                f"{MAX_LIVE_OBJECTS} live event objects, and this one was dropped to "
                "make room",
                "evicted",
            )
        return f"nothing is registered for event {event_id!r}", "not-found"


class InBrowserEventProxy:
    """Plays the part of the browser for a layout which is running inside it"""

    def __init__(self, registry: EventProxyRegistry | None = None) -> None:
        self.registry = EventProxyRegistry() if registry is None else registry
        self._deliver: Any = None

    def bind(self, layout: Any) -> None:
        """Route answers back into ``layout.handle_event_proxy_response``"""
        self._deliver = layout.handle_event_proxy_response

    # -- dispatching --------------------------------------------------------

    def event_data(self, args: tuple[Any, ...], options: dict[str, Any]) -> list[Any]:
        """The ``data`` list to deliver for a dispatched browser event

        Nothing about the object which triggered the event travels with it; only an id
        does, plus whatever small scalar the page can volunteer up front - which in
        practice means the event ``type``, the one property a handler nearly always
        wants and which stays true even after the object behind it is forgotten.

        Whatever was not an object is handed over as it arrived, and a flag the element's
        handler carried is carried out here, since this is the side of the boundary which
        can actually ask the browser to honour it.
        """
        data: list[Any] = []
        for index, argument in enumerate(args):
            if not _is_js_object(argument):
                data.append(argument)
                continue
            if index == 0:
                _apply_flags(argument, options)
            marker: dict[str, Any] = {
                EVENT_MARKER_KEY: {"id": self.registry.register(argument)}
            }
            event_type = _safe_type(argument)
            if event_type is not None:
                # the one property worth sending up front, and only when it is one
                marker["type"] = event_type
            data.append(marker)
        return data

    # -- answering ----------------------------------------------------------

    async def send(self, message: dict[str, Any]) -> None:
        """The layout's live event sender: answer here instead of over a connection"""
        if not message or message.get("type") != EVENT_PROXY_REQUEST_TYPE:
            return
        # The requests are carried out first and only then is the registry swept.
        # Carrying one out is the proof that its object is still wanted, so sweeping
        # beforehand would delete the very object a message had arrived to ask about.
        try:
            self._answer(message)
        finally:
            self.registry.prune()

    def _answer(self, message: dict[str, Any]) -> None:
        requests = message.get("requests")
        if not isinstance(requests, list):
            response = self.resolve(message)
            if message.get("reply") is not False:
                self._reply(response)
            return

        responses = []
        for index, request in enumerate(requests):
            if not request or not isinstance(request, dict):
                continue
            if index >= MAX_REQUESTS_PER_MESSAGE:
                response = _refuse(
                    request,
                    "a single message may not ask for more than "
                    f"{MAX_REQUESTS_PER_MESSAGE} things at once",
                )
            else:
                response = self.resolve(request)
            if request.get("reply") is not False:
                responses.append(response)
        if responses:
            self._reply({"type": EVENT_PROXY_RESPONSE_TYPE, "responses": responses})

    def _reply(self, response: dict[str, Any]) -> None:
        if self._deliver is not None:
            self._deliver(response)

    def resolve(self, message: dict[str, Any]) -> dict[str, Any]:
        """Carry out one ``event-proxy-request`` and produce the answer to it"""
        request_id = message.get("requestId")
        request_id = request_id if isinstance(request_id, str) else ""

        def reply(ok: bool, **extra: Any) -> dict[str, Any]:
            return {
                "type": EVENT_PROXY_RESPONSE_TYPE,
                "requestId": request_id,
                "ok": ok,
                "error": None,
                "code": None,
                **extra,
            }

        event_id = message.get("eventId")
        event_id = event_id if isinstance(event_id, str) else ""
        entry = self.registry.get(event_id)
        if entry is None:
            error, code = self.registry.missing(event_id)
            return reply(False, error=error, code=code)

        path = [str(segment) for segment in (message.get("path") or [])]
        max_depth = _allowed_depth(message.get("maxDepth"))

        try:
            if message.get("call"):
                result = self._call(entry, path, message.get("args") or [], max_depth)
                # Whatever the layout was handed may have come out of this value, so it
                # has to stay around or the path to it leads nowhere.
                entry.remember_call(path, result)
                return reply(
                    True,
                    value=serialize_value(
                        result, event_id, path=path, max_depth=max_depth
                    ),
                )

            if not path:
                return reply(
                    True,
                    value=serialize_value(
                        entry.value, event_id, path=path, max_depth=max_depth
                    ),
                )

            value = read_path(entry, path)
            if callable(value) and not isinstance(value, type):
                return reply(True, value=_reference(event_id, path, True))
            return reply(
                True,
                value=serialize_value(value, event_id, path=path, max_depth=max_depth),
            )
        except ProxyError as error:
            return reply(False, error=str(error), code=error.code)
        except Exception as error:  # never let a read take the page down
            return reply(False, error=str(error), code="access")

    def _call(
        self, entry: LiveObject, path: list[str], args: list[Any], max_depth: int
    ) -> Any:
        if not path:
            msg = "the event object itself cannot be called"
            raise ProxyAccessError(msg)
        parent = entry.value
        for index in range(len(path) - 1):
            parent = _step_down(entry, parent, path, index)
        name = path[-1]
        if is_blocked_member(name):
            msg = f'calling "{name}" is not allowed'
            raise ProxyAccessError(msg)
        method = _read(parent, name)
        if not callable(method):
            msg = f"{name!r} is not a function"
            raise ProxyAccessError(msg)
        return method(
            *[self._read_argument(argument, max_depth, 0) for argument in args]
        )

    def _read_argument(self, argument: Any, max_depth: int, depth: int) -> Any:
        """Turn a reference back into the live object it names, for a method call"""
        if depth > max_depth:
            msg = f"an argument was nested more deeply than {max_depth} levels"
            raise ProxyAccessError(msg)
        if isinstance(argument, dict):
            raw = argument.get(EVENT_REFERENCE_KEY)
            if isinstance(raw, dict) and isinstance(raw.get("eventId"), str):
                target_id = raw["eventId"]
                target = self.registry.get(target_id)
                if target is None:
                    error, code = self.registry.missing(target_id)
                    raise (
                        ProxyEvictedError(error)
                        if code == "evicted"
                        else ProxyNotFoundError(error)
                    )
                return read_path(target, [str(s) for s in (raw.get("path") or [])])
            return {
                key: self._read_argument(item, max_depth, depth + 1)
                for key, item in argument.items()
            }
        if isinstance(argument, list):
            return [
                self._read_argument(item, max_depth, depth + 1) for item in argument
            ]
        return argument


def _apply_flags(event_object: Any, options: dict[str, Any]) -> None:
    """Honour ``preventDefault`` and friends on the object which triggered the event

    These are the element's instructions rather than the handler's, and only this side of
    the boundary can act on them: by the time a handler on a server sees the flag, the
    default action has long since happened.
    """
    for option, method in (
        ("preventDefault", "preventDefault"),
        ("stopPropagation", "stopPropagation"),
        ("stopImmediatePropagation", "stopImmediatePropagation"),
    ):
        if not options.get(option):
            continue
        try:
            getattr(event_object, method)()
        except Exception as error:  # a non-cancelable event is not an error
            logger.debug(f"Could not {method}() on a dispatched event: {error}")


def _safe_type(event_object: Any) -> str | None:
    """The event's ``type``, if it can be had without any risk"""
    try:
        value = getattr(event_object, "type", None)
    except Exception:
        return None
    return value if isinstance(value, str) else None


def _allowed_depth(proposed: Any) -> int:
    """Read the depth a request asked for as a sane one, whatever it actually said

    A negative, non-numeric, or simply enormous value would otherwise turn the bound
    which is here to protect the page into the way past it. A request which did not say
    at all is answered with the shallowest thing there is, since guessing here would
    mean a malformed message being handed more of the page than it asked for.
    """
    if isinstance(proposed, bool) or not isinstance(proposed, int | float):
        return 0
    if math.isnan(proposed) or math.isinf(proposed):
        return 0
    return min(max(int(proposed), 0), MAX_ALLOWED_DEPTH)


def _refuse(request: Any, error: str) -> dict[str, Any]:
    """Answer a request which is not going to be carried out

    Whatever wanted an answer gets one, because leaving it unanswered would have the
    layout sit there until its own timeout and count a page which is perfectly awake
    against it.
    """
    request_id = request.get("requestId") if isinstance(request, dict) else None
    return {
        "type": EVENT_PROXY_RESPONSE_TYPE,
        "requestId": request_id if isinstance(request_id, str) else "",
        "ok": False,
        "error": error,
        "code": "access",
    }
