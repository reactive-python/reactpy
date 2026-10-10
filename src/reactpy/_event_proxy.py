"""Client-backed ("live") proxies for browser events.

Historically an event handler was handed a plain :class:`reactpy.types.Event` - a
snapshot of the JavaScript ``Event`` object built by the ``event-to-object`` package.
Snapshots are cheap and never block, but they are frozen at the moment the event was
dispatched: methods such as ``focus()`` or ``composedPath()`` cannot be called from
Python, and any property that the snapshot left out is simply gone.

This module implements the machinery which lets a handler reach *live* into the browser
instead. When the client supports it, each item of a ``layout-event`` message carries a
small marker next to the usual snapshot::

    {
        "type": "layout-event",
        "target": "key-path:onClick",
        "data": [
            {
                "type": "click",
                "target": {"tagName": "INPUT", "value": "hello"},
                "__reactpy_event__": {"id": "5b1c..."},
            }
        ],
    }

On receipt, ReactPy swaps that dictionary for a :class:`SyncEvent` or
:class:`AsyncEvent` - both are ``dict`` subclasses which *also* hold the snapshot.
Reading an attribute returns a lazily resolved :class:`EventProxy` whose value is
fetched from the browser only when it is actually needed:

.. code-block:: python

    async def on_click(event: AsyncEvent):
        # one round trip: read "target.value" from the live DOM node
        value = await event.target.value
        # one round trip: call "focus()" on the live DOM node
        await event.target.focus()
        # nothing is sent for values which the snapshot already contains
        print(event["type"])

Which flavour a handler receives is decided by the handler itself: ``async def``
handlers get :class:`AsyncEvent` (resolve with ``await`` or ``.resolve()``), plain
``def`` handlers get :class:`SyncEvent` whose accessors block - transparently running
the whole handler in a worker thread when it needs the value of a live property.

Resolution travels over the existing connection with two extra message types:

.. code-block:: json

    {"type": "event-proxy-request", "requestId": "...", "eventId": "...",
     "path": ["target", "value"], "call": false, "args": [], "reply": true,
     "maxDepth": 10}

    {"type": "event-proxy-response", "requestId": "...", "ok": true,
     "value": "hello", "error": null, "code": null}

Objects which cannot be serialized (DOM nodes, functions, ...) come back as a
reference - ``{"__reactpy_ref__": {"path": ["target"]}}`` - which ReactPy turns into
another proxy, so arbitrarily deep structures can be walked on demand.
"""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Awaitable, Callable, Mapping, Sequence
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FuturesTimeoutError
from logging import getLogger
from typing import TYPE_CHECKING, Any, Generic, NoReturn, TypeVar
from uuid import uuid4

from reactpy.config import (
    REACTPY_EVENT_PROXY_MAX_DEPTH,
    REACTPY_EVENT_PROXY_MAX_TIMEOUTS,
    REACTPY_EVENT_PROXY_TIMEOUT,
)

logger = getLogger(__name__)

EVENT_PROXY_REQUEST_TYPE = "event-proxy-request"
"""The ``type`` of a server to client live event access message"""

EVENT_PROXY_RESPONSE_TYPE = "event-proxy-response"
"""The ``type`` of a client to server live event access result message"""

EVENT_MARKER_KEY = "__reactpy_event__"
"""The key used to mark event data as being backed by a live client side object"""

EVENT_REFERENCE_KEY = "__reactpy_ref__"
"""The key used to mark a value as a reference to a live client side object"""

_T = TypeVar("_T")
_MISSING = object()

SendCoroutine = Callable[[dict[str, Any]], Awaitable[None]]
"""Sends a single message to the client which owns a given event"""


class EventProxyError(RuntimeError):
    """Base class for failures which occur while resolving live event data"""


class EventProxyUnavailable(EventProxyError):
    """The client which dispatched this event cannot serve live event access"""


class EventProxyTimeout(EventProxyError):
    """The client did not answer a live event access request in time"""


class EventProxyNotFound(EventProxyError):
    """The browser object this proxy refers to is no longer available"""


class EventProxyAccessError(EventProxyError):
    """The client refused or failed to resolve the requested path"""


class EventProxyBlocked(EventProxyError):
    """Synchronous live event access was attempted from the event loop thread

    A synchronous event handler which needs a live value is run in a worker thread by
    ReactPy. Seeing this error means that a blocking access was attempted somewhere
    which ReactPy could not run off of the event loop - typically from an ``async def``
    handler using a :class:`SyncEvent`. Prefer ``await`` on an :class:`AsyncEvent`.
    """


class EventProxyBackend:
    """Sends live event access requests and routes the answers back to waiters

    One backend is owned by each connected client (a layout). It knows how to talk to
    the browser and keeps track of every request which is currently in flight.
    """

    def __init__(self) -> None:
        self._send: SendCoroutine | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread_id: int | None = None
        self._pending: dict[str, Future] = {}
        self._send_tasks: set[Any] = set()
        self._timeouts = 0
        self._disabled = False

    @property
    def available(self) -> bool:
        """Whether live event access may currently be attempted"""
        return self._send is not None and not self._disabled

    @property
    def disabled(self) -> bool:
        """Whether live event access has been switched off for this connection"""
        return self._disabled

    def set_sender(self, send: SendCoroutine) -> None:
        """Bind the coroutine which sends a single message to the client

        This must be called from the event loop which runs the associated layout since
        live access needs to know both *how* and *from which thread* to talk to the
        browser.
        """
        self._send = send
        self._loop = asyncio.get_running_loop()
        self._loop_thread_id = threading.get_ident()

    def disable(self, reason: str) -> None:
        """Stop attempting live access, for example because the client went away"""
        if not self._disabled:
            self._disabled = True
            logger.warning(f"Live event access disabled - {reason}")
        self._abandon_pending(reason)

    def close(self) -> None:
        """Abandon all in-flight requests (called when the layout shuts down)"""
        self._disabled = True
        self._abandon_pending("the layout was closed")

    def _abandon_pending(self, reason: str) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(EventProxyUnavailable(reason))
        self._pending.clear()

    def handle_response(self, message: Mapping[str, Any]) -> bool:
        """Route a ``event-proxy-response`` message to whoever is waiting for it

        Returns :data:`True` if the message was meant for this backend.
        """
        if message.get("type") != EVENT_PROXY_RESPONSE_TYPE:
            return False

        request_id = message.get("requestId")
        future = (
            self._pending.pop(request_id, None) if isinstance(request_id, str) else None
        )
        if future is None:
            # Either the request timed out or the layout was closed while it was in
            # flight. Either way there is nobody left to deliver the answer to.
            logger.debug(
                f"Ignored live event response to unknown request {request_id!r}"
            )
            return True

        if not future.done():
            future.set_result(
                {
                    "ok": bool(message.get("ok")),
                    "value": message.get("value"),
                    "error": message.get("error"),
                    "code": message.get("code"),
                }
            )
        return True

    async def resolve(
        self,
        event_id: str,
        path: Sequence[str | int],
        call: bool = False,
        args: Sequence[Any] = (),
        sync: bool = False,
    ) -> Any:
        """Resolve ``path`` against the client side event (awaited from the loop)"""
        request_id, message, future = self._begin(
            event_id, path, call, args, reply=True
        )
        self._submit(message, future, request_id)
        if future is None:  # nocov - reply=True always yields a future
            return None
        try:
            payload = await asyncio.wait_for(
                asyncio.wrap_future(future), REACTPY_EVENT_PROXY_TIMEOUT.current
            )
        except (TimeoutError, FuturesTimeoutError):
            self._handle_timeout(request_id, event_id, path)
        return self._to_value(payload, event_id, path, sync)

    def resolve_blocking(
        self,
        event_id: str,
        path: Sequence[str | int],
        call: bool = False,
        args: Sequence[Any] = (),
    ) -> Any:
        """Resolve ``path`` by blocking the calling (non-loop) thread until answered"""
        if (
            self._loop_thread_id is not None
            and threading.get_ident() == self._loop_thread_id
        ):
            msg = (
                f"cannot synchronously resolve {list(path)!r} of event {event_id!r} from "
                "the event loop thread - access live values from a synchronous event "
                "handler, or await them from an asynchronous one"
            )
            raise EventProxyBlocked(msg)

        request_id, message, future = self._begin(
            event_id, path, call, args, reply=True
        )
        if future is None:  # nocov - reply=True always yields a future
            return None
        self._submit(message, future, request_id)
        try:
            payload = future.result(timeout=REACTPY_EVENT_PROXY_TIMEOUT.current)
        except (TimeoutError, FuturesTimeoutError):
            self._handle_timeout(request_id, event_id, path)
        return self._to_value(payload, event_id, path, sync=True)

    def notify(
        self,
        event_id: str,
        path: Sequence[str | int],
        args: Sequence[Any] = (),
    ) -> None:
        """Call a client side method without waiting for its result (best effort)"""
        try:
            request_id, message, future = self._begin(
                event_id, path, True, args, reply=False
            )
        except EventProxyError:
            logger.debug(
                f"Could not schedule live call to {list(path)!r} of {event_id!r}"
            )
            return
        self._submit(message, future, request_id)

    # -- internals --------------------------------------------------------

    def _begin(
        self,
        event_id: str,
        path: Sequence[str | int],
        call: bool,
        args: Sequence[Any],
        reply: bool,
    ) -> tuple[str, dict[str, Any], Future | None]:
        if not self.available:
            msg = f"live access to event {event_id!r} is unavailable"
            raise EventProxyUnavailable(msg)
        if call and not path:
            msg = "the event object itself cannot be called"
            raise EventProxyAccessError(msg)

        request_id = uuid4().hex
        message: dict[str, Any] = {
            "type": EVENT_PROXY_REQUEST_TYPE,
            "requestId": request_id,
            "eventId": event_id,
            "path": [str(segment) for segment in path],
            "call": call,
            "args": [serialize_argument(argument) for argument in args],
            "reply": reply,
            "maxDepth": REACTPY_EVENT_PROXY_MAX_DEPTH.current,
        }
        future: Future | None = None
        if reply:
            future = Future()
            self._pending[request_id] = future
        return request_id, message, future

    def _submit(
        self,
        message: dict[str, Any],
        future: Future | None,
        request_id: str,
    ) -> None:
        loop, send = self._loop, self._send
        if loop is None or send is None:
            self._discard(request_id)
            if future is not None and not future.done():
                future.set_exception(
                    EventProxyUnavailable("no sender is bound to this connection")
                )
            return

        if threading.get_ident() == self._loop_thread_id:
            task = loop.create_task(self._send_message(message, future))
            self._send_tasks.add(task)
            task.add_done_callback(self._send_tasks.discard)
        else:
            asyncio.run_coroutine_threadsafe(self._send_message(message, future), loop)

    async def _send_message(
        self, message: dict[str, Any], future: Future | None
    ) -> None:
        send = self._send
        if send is None:  # nocov - guarded by _submit
            return
        try:
            await send(message)
        except Exception as error:  # any send failure kills live access for this client
            self.disable(f"failed to send a live event request ({error})")

    def _discard(self, request_id: str) -> None:
        self._pending.pop(request_id, None)

    def _handle_timeout(
        self, request_id: str, event_id: str, path: Sequence[str | int]
    ) -> NoReturn:
        self._discard(request_id)
        self._timeouts += 1
        max_timeouts = REACTPY_EVENT_PROXY_MAX_TIMEOUTS.current
        if max_timeouts > 0 and self._timeouts >= max_timeouts:
            self.disable(
                f"{self._timeouts} consecutive live event requests went unanswered"
            )
        msg = (
            f"the client did not answer the request for {list(path)!r} of event "
            f"{event_id!r} within {REACTPY_EVENT_PROXY_TIMEOUT.current}s"
        )
        raise EventProxyTimeout(msg)

    def _to_value(
        self,
        payload: Mapping[str, Any],
        event_id: str,
        path: Sequence[str | int],
        sync: bool,
    ) -> Any:
        if not payload.get("ok"):
            code = payload.get("code") or "access"
            error = payload.get("error") or "the client did not provide a reason"
            message = f"could not resolve {list(path)!r} of event {event_id!r}: {error}"
            if code == "not-found":
                raise EventProxyNotFound(message)
            if code == "timeout":
                self._handle_timeout("", event_id, path)
            raise EventProxyAccessError(message)

        self._timeouts = 0
        return deserialize_value(payload.get("value"), event_id, self, sync)


def serialize_argument(value: Any) -> Any:
    """Prepare a Python value to be handed to a client side method"""
    if isinstance(value, EventProxy):
        return {
            EVENT_REFERENCE_KEY: {
                "eventId": value.event_id,
                "path": [str(segment) for segment in value.path],
            }
        }
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Mapping):
        return {str(key): serialize_argument(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [serialize_argument(item) for item in value]

    try:
        json.dumps(value)
    except (TypeError, ValueError) as error:
        msg = f"cannot pass {value!r} to the client: {error}"
        raise EventProxyAccessError(msg) from error
    return value


def deserialize_value(
    value: Any,
    event_id: str,
    backend: EventProxyBackend,
    sync: bool,
    depth: int = 0,
) -> Any:
    """Turn a client supplied value into data, replacing references with proxies"""
    if depth > REACTPY_EVENT_PROXY_MAX_DEPTH.current:
        msg = (
            f"live event data for event {event_id!r} is nested more deeply than "
            f"{REACTPY_EVENT_PROXY_MAX_DEPTH.current} levels"
        )
        raise EventProxyAccessError(msg)

    if isinstance(value, Mapping):
        reference = value.get(EVENT_REFERENCE_KEY)
        if isinstance(reference, Mapping):
            child_class = SyncEventProxy if sync else AsyncEventProxy
            child = child_class(
                backend,
                str(reference.get("eventId", event_id)),
                tuple(reference.get("path", ())),
            )
            child._reactpy_callable = bool(reference.get("callable"))
            return child
        return {
            key: deserialize_value(item, event_id, backend, sync, depth + 1)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            deserialize_value(item, event_id, backend, sync, depth + 1)
            for item in value
        ]

    return value


class _EventProxyBase(dict, Generic[_T]):
    """A live, lazily resolved view onto a browser object

    Instances are ``dict`` subclasses which hold on to whatever the client chose to
    serialize when the event was dispatched (the "snapshot"). Attribute access returns
    further proxies for anything the snapshot does not already answer with a plain
    value, so a chain such as ``event.target.value`` costs a single round trip - and
    only when the value is genuinely needed.
    """

    _reactpy_sync: bool = False
    """Whether resolving this proxy blocks (sync) or must be awaited (async)"""

    def __init__(
        self,
        backend: EventProxyBackend,
        event_id: str,
        path: Sequence[str | int] = (),
        snapshot: Mapping[str, Any] | None = None,
        flags: dict[str, bool] | None = None,
    ) -> None:
        dict.__init__(self, snapshot or {})
        self._reactpy_backend = backend
        self._reactpy_event_id = event_id
        self._reactpy_path: tuple[str | int, ...] = tuple(path)
        self._reactpy_flags = {} if flags is None else flags
        self._reactpy_debounce: int | None = None
        self._reactpy_callable = False

    # -- identity ---------------------------------------------------------

    @property
    def event_id(self) -> str:
        """The client assigned identifier of the event this proxy belongs to"""
        return self._reactpy_event_id

    @property
    def path(self) -> tuple[str | int, ...]:
        """The property path, relative to the event object, this proxy points at"""
        return self._reactpy_path

    @property
    def backend(self) -> EventProxyBackend:
        """The connection which serves this proxy"""
        return self._reactpy_backend

    @property
    def has_snapshot(self) -> bool:
        """Whether the client already gave us the value of this proxy"""
        return bool(dict.__len__(self))

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(event_id={self._reactpy_event_id!r}, "
            f"path={list(self._reactpy_path)!r}, snapshot={dict.__repr__(self)})"
        )

    def __dir__(self) -> list[str]:
        return sorted(
            {
                *dir(type(self)),
                *(key for key in dict.keys(self) if isinstance(key, str)),
            }
        )

    # -- child access -----------------------------------------------------

    def _reactpy_snapshot_value(self, segment: str | int) -> Any:
        try:
            return dict.__getitem__(self, segment)
        except KeyError:
            return _MISSING

    def _reactpy_make_child(
        self, segment: str | int, snapshot: Mapping[str, Any] | None = None
    ) -> _EventProxyBase[Any]:
        child_class: type[_EventProxyBase[Any]] = (
            SyncEventProxy if self._reactpy_sync else AsyncEventProxy
        )
        child = child_class(
            self._reactpy_backend,
            self._reactpy_event_id,
            (*self._reactpy_path, segment),
            flags=self._reactpy_flags,
        )
        if snapshot is None:
            value = self._reactpy_snapshot_value(segment)
            snapshot = value if isinstance(value, Mapping) else {}
        reference = (
            snapshot.get(EVENT_REFERENCE_KEY) if isinstance(snapshot, Mapping) else None
        )
        if isinstance(reference, Mapping):
            # The snapshot only points at what the browser still holds - hand back a
            # real proxy for it rather than a dict containing the marker.
            path = tuple(reference.get("path", ())) or (*self._reactpy_path, segment)
            child = child_class(
                self._reactpy_backend,
                str(reference.get("eventId", self._reactpy_event_id)),
                path,
                flags=self._reactpy_flags,
            )
            child._reactpy_callable = bool(reference.get("callable"))
            return child
        dict.update(child, snapshot)
        return child

    def _reactpy_wrap_sequence(
        self, segment: str | int, value: Sequence[Any]
    ) -> list[Any]:
        """Copy a list of snapshot data, promoting object entries to child proxies"""
        parent = self._reactpy_make_child(segment)
        items: list[Any] = []
        for index, item in enumerate(value):
            if isinstance(item, Mapping):
                items.append(parent._reactpy_make_child(str(index), item))
            elif isinstance(item, list | tuple):
                items.append(parent._reactpy_wrap_sequence(str(index), item))
            else:
                items.append(item)
        return items

    def _reactpy_child_or_value(self, segment: str | int) -> Any:
        """Return the snapshot value, or a proxy for whatever the browser holds"""
        value = self._reactpy_snapshot_value(segment)
        if value is _MISSING:
            return self._reactpy_resolve_segment(segment)
        if isinstance(value, Mapping):
            return self._reactpy_make_child(segment)
        if isinstance(value, list | tuple):
            return self._reactpy_wrap_sequence(segment, value)
        return value

    def _reactpy_resolve_segment(self, segment: str | int) -> Any:
        """Read something the snapshot does not know about

        The asynchronous flavour stays lazy here; the synchronous one asks the browser
        right away so that handlers always deal with real values.
        """
        return self._reactpy_make_child(segment)

    def _reactpy_walk_snapshot(self, segments: Sequence[str]) -> Any:
        """Follow ``segments`` through the snapshot, or return ``_MISSING``"""
        node: Any = self
        for segment in segments:
            if isinstance(node, dict):
                if not dict.__contains__(node, segment):
                    return _MISSING
                # bypass proxy __getitem__ so nested data stays plain JSON
                node = dict.__getitem__(node, segment)
            elif isinstance(node, Mapping):
                if segment not in node:
                    return _MISSING
                node = node[segment]
            elif isinstance(node, Sequence) and not isinstance(node, str | bytes):
                try:
                    node = node[int(segment)]
                except (ValueError, IndexError):
                    return _MISSING
            else:
                return _MISSING
        return node

    @staticmethod
    def _reactpy_normalize_path(path: str | Sequence[Any]) -> list[str]:
        if isinstance(path, str):
            return [segment for segment in path.split(".") if segment]
        return [str(segment) for segment in path]

    def _reactpy_invoke(
        self, name: str, args: Sequence[Any] = (), wait: bool = False
    ) -> Any:
        """Call the client side method ``name`` on the object this proxy points at"""
        path = (*self._reactpy_path, name)
        backend = self._reactpy_backend
        if wait:
            return backend.resolve(
                self._reactpy_event_id, path, call=True, args=args, sync=False
            )
        backend.notify(self._reactpy_event_id, path, args)
        return None

    # -- event level conveniences -----------------------------------------

    def preventDefault(self) -> None:
        """Prevent the default action of the underlying DOM event

        The matching JavaScript call is scheduled on the client but is *not* waited
        for. Use :func:`reactpy.event`'s ``prevent_default=True`` if the action must be
        cancelled before the browser carries on.
        """
        self._reactpy_flags["preventDefault"] = True
        self._reactpy_invoke("preventDefault")

    def stopPropagation(self) -> None:
        """Stop the underlying DOM event from propagating further up the tree"""
        self._reactpy_flags["stopPropagation"] = True
        self._reactpy_invoke("stopPropagation")

    def stopImmediatePropagation(self) -> None:
        """Also stop any remaining listeners of the underlying DOM event"""
        self._reactpy_flags["stopPropagation"] = True
        self._reactpy_flags["stopImmediatePropagation"] = True
        self._reactpy_invoke("stopImmediatePropagation")

    @property
    def defaultPrevented(self) -> bool:
        """Whether :meth:`preventDefault` has been called for this event"""
        return bool(
            self._reactpy_flags.get("preventDefault")
            or dict.get(self, "defaultPrevented", False),
        )

    @property
    def propagationStopped(self) -> bool:
        """Whether :meth:`stopPropagation` has been called for this event"""
        return bool(
            self._reactpy_flags.get("stopPropagation")
            or dict.get(self, "propagationStopped", False),
        )

    @property
    def debounce(self) -> int | None:
        """Rate limit (in milliseconds) applied to server driven value updates"""
        return self._reactpy_debounce

    @debounce.setter
    def debounce(self, value: int | None) -> None:
        self._reactpy_debounce = value

    # -- dict like behaviour ----------------------------------------------

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_reactpy") or (
            name.startswith("__") and name.endswith("__")
        ):
            # Never resolve internals or interpreter lookups against the browser
            raise AttributeError(name)
        return self._reactpy_child_or_value(name)

    def __getitem__(self, key: Any) -> Any:
        return self._reactpy_child_or_value(key)

    def __bool__(self) -> bool:
        return bool(dict.__len__(self)) or bool(self._reactpy_path)

    # -- resolution (implemented by the sync and async flavours) ----------

    def _reactpy_resolve_path(self, call: bool, args: Sequence[Any]) -> Any:
        msg = f"{type(self).__name__} cannot resolve live event data"
        raise NotImplementedError(msg)

    def _reactpy_call_method(self, name: str, args: Sequence[Any]) -> Any:
        path = (*self._reactpy_path, name)
        backend = self._reactpy_backend
        if self._reactpy_sync:
            return backend.resolve_blocking(
                self._reactpy_event_id, path, call=True, args=args
            )
        return backend.resolve(
            self._reactpy_event_id, path, call=True, args=args, sync=False
        )

    def composedPath(self) -> Any:  # the JavaScript method name is kept as-is
        """Return the event's path, resolving on the client if needed

        This blocks for a :class:`SyncEventProxy` and must be awaited for an
        :class:`AsyncEventProxy`.
        """
        return self._reactpy_call_method("composedPath", ())

    def _reactpy_description(self) -> str:
        return (
            f"{type(self).__name__} for {list(self._reactpy_path)!r} of event "
            f"{self._reactpy_event_id!r}"
        )

    def _reactpy_require_snapshot(self, action: str) -> None:
        """Complain about an operation which needs a value we do not have yet"""
        if self._reactpy_backend.available:
            msg = (
                f"cannot {action} {self._reactpy_description()} because nothing is "
                "known about it yet - await the proxy (or call .resolve() on it) first"
            )
            raise EventProxyAccessError(msg)


class AsyncEventProxy(_EventProxyBase[_T]):
    """The asynchronous flavour of a live event object

    Values are pulled from the browser with ``await``::

        async def on_input(event: AsyncEvent):
            value = await event.target.value
            await event.target.focus()
    """

    _reactpy_sync = False

    def _reactpy_resolve_path(self, call: bool, args: Sequence[Any]) -> Any:
        return self._reactpy_backend.resolve(
            self._reactpy_event_id,
            self._reactpy_path,
            call=call,
            args=args,
            sync=False,
        )

    def resolve(self) -> Awaitable[_T]:
        """Fetch the value this proxy currently points at from the browser"""
        return self._reactpy_resolve_path(False, ())

    async def read(self, path: str | Sequence[Any], default: Any = _MISSING) -> Any:
        """Return the value at ``path`` whether or not the snapshot knows it

        Unlike awaiting an attribute, this always works - including for values which
        the snapshot already answered with a plain ``str``, ``bool`` or ``None``::

            async def on_input(event: AsyncEvent):
                value = await event.read("target.value")
        """
        segments = self._reactpy_normalize_path(path)
        value = self._reactpy_walk_snapshot(segments)
        if value is not _MISSING:
            return value
        try:
            return await self._reactpy_backend.resolve(
                self._reactpy_event_id,
                (*self._reactpy_path, *segments),
                call=False,
                args=(),
                sync=False,
            )
        except EventProxyError:
            if default is _MISSING:
                raise
            return default

    def __await__(self) -> Any:
        return self._reactpy_resolve_path(False, ()).__await__()

    def __call__(self, *args: Any) -> Awaitable[Any]:
        """Call the client side method this proxy currently points at"""
        return self._reactpy_resolve_path(True, args)

    def __len__(self) -> int:
        if not dict.__len__(self):
            self._reactpy_require_snapshot("measure")
        return dict.__len__(self)

    def __iter__(self) -> Any:
        if not dict.__len__(self):
            self._reactpy_require_snapshot("iterate over")
        return dict.__iter__(self)

    def __contains__(self, key: Any) -> bool:
        if dict.__contains__(self, key):
            return True
        if not dict.__len__(self):
            self._reactpy_require_snapshot("test membership of")
        return False


class SyncEventProxy(_EventProxyBase[_T]):
    """The synchronous flavour of a live event object

    Accessing something the snapshot does not already know about blocks until the
    browser answers. ReactPy runs synchronous event handlers in a worker thread for
    exactly this reason, so the event loop is never stalled.
    """

    _reactpy_sync = True

    def _reactpy_resolve_segment(self, segment: str | int) -> Any:
        """Read a value the snapshot does not have, blocking until the browser answers"""
        try:
            value = self._reactpy_backend.resolve_blocking(
                self._reactpy_event_id,
                (*self._reactpy_path, segment),
                call=False,
                args=(),
            )
        except (
            EventProxyTimeout,
            EventProxyNotFound,
            EventProxyAccessError,
            EventProxyUnavailable,
        ):
            # The browser could not tell us - hand back an (empty) proxy so that
            # repr(), logging and "in" checks keep working.
            logger.debug(
                f"Falling back to snapshot data for {list(self._reactpy_path)!r}"
                f" + {segment!r}",
                exc_info=True,
            )
            return self._reactpy_make_child(segment)

        if isinstance(value, _EventProxyBase):
            return value
        if isinstance(value, Mapping):
            return self._reactpy_make_child(segment, value)
        if isinstance(value, list | tuple):
            return self._reactpy_wrap_sequence(segment, value)
        return value

    def _reactpy_resolve_path(self, call: bool, args: Sequence[Any]) -> Any:
        return self._reactpy_backend.resolve_blocking(
            self._reactpy_event_id, self._reactpy_path, call=call, args=args
        )

    def resolve(self) -> _T:
        """Fetch the value this proxy currently points at from the browser"""
        return self._reactpy_resolve_path(False, ())

    def read(self, path: str | Sequence[Any], default: Any = _MISSING) -> Any:
        """Return the value at ``path`` whether or not the snapshot knows it

        Blocking, like every other accessor on this class::

            def on_input(event: SyncEvent):
                value = event.read("target.value")
        """
        segments = self._reactpy_normalize_path(path)
        value = self._reactpy_walk_snapshot(segments)
        if value is not _MISSING:
            return value
        try:
            return self._reactpy_backend.resolve_blocking(
                self._reactpy_event_id,
                (*self._reactpy_path, *segments),
                call=False,
                args=(),
            )
        except EventProxyError:
            if default is _MISSING:
                raise
            return default

    def __call__(self, *args: Any) -> Any:
        """Call the client side method this proxy currently points at"""
        return self._reactpy_resolve_path(True, args)

    def _reactpy_resolved_or_self(self) -> Any:
        """The live value if we do not have a snapshot for it, else this proxy"""
        if dict.__len__(self) or not self._reactpy_backend.available:
            return self
        try:
            value = self._reactpy_resolve_path(False, ())
        except EventProxyError:
            logger.debug(
                f"Could not resolve {self._reactpy_description()}", exc_info=True
            )
            return self
        # a reference to something else (an object or a function) says nothing about
        # how this proxy should be printed or compared
        return self if isinstance(value, _EventProxyBase) else value

    def __eq__(self, other: Any) -> Any:
        if isinstance(other, _EventProxyBase):
            if (self._reactpy_event_id, self._reactpy_path) == (
                other._reactpy_event_id,
                other._reactpy_path,
            ):
                return True
            return dict.__eq__(self, other)
        value = self._reactpy_resolved_or_self()
        if value is self:
            return dict.__eq__(self, other)
        return bool(value == other)

    def __ne__(self, other: Any) -> Any:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    __hash__ = None  # type: ignore[assignment]

    def __str__(self) -> str:
        value = self._reactpy_resolved_or_self()
        return dict.__repr__(self) if value is self else str(value)

    def __format__(self, format_spec: str) -> str:
        value = self._reactpy_resolved_or_self()
        if value is self:
            return dict.__repr__(self)
        return format(value, format_spec)

    def __len__(self) -> int:
        if dict.__len__(self):
            return dict.__len__(self)
        return len(self._reactpy_resolved_or_self())

    def __iter__(self) -> Any:
        if dict.__len__(self):
            return dict.__iter__(self)
        value = self._reactpy_resolved_or_self()
        return dict.__iter__(self) if value is self else iter(value)

    def __contains__(self, key: Any) -> bool:
        if dict.__contains__(self, key):
            return True
        if dict.__len__(self) or not self._reactpy_backend.available:
            return False
        try:
            return bool(key in self._reactpy_resolve_path(False, ()))
        except EventProxyError:
            return False


EventProxy = _EventProxyBase
"""The base class of every lazily resolved live event object"""


if TYPE_CHECKING:
    _ElementMembers = dict[str, Any]


class AsyncEvent(AsyncEventProxy[_T]):
    """The event object handed to ``async def`` event handlers

    A ``dict`` subclass which holds the snapshot the client took when the event was
    dispatched *and* knows how to reach back into the browser for anything missing::

        async def on_key_down(event: AsyncEvent):
            if await event.read("key") == "Enter":
                await event.target.focus()
                print(await event.target.value)

    Every member below is a best-effort hint for editors and type checkers. At runtime
    any property of any browser object can be read - unlisted ones simply resolve to
    :class:`AsyncEventProxy`.
    """

    if TYPE_CHECKING:
        # -- identity -----------------------------------------------------
        type: str
        target: AsyncEventProxy[Any]
        currentTarget: AsyncEventProxy[Any]
        srcElement: AsyncEventProxy[Any]
        relatedTarget: AsyncEventProxy[Any]
        view: AsyncEventProxy[Any]
        # -- flags --------------------------------------------------------
        # ``defaultPrevented`` and ``propagationStopped`` are typed by the base class.
        bubbles: bool
        cancelable: bool
        composed: bool
        cancelBubble: bool
        isTrusted: bool
        eventPhase: int
        timeStamp: float
        returnValue: Any
        detail: Any
        # -- mouse --------------------------------------------------------
        button: int
        buttons: int
        clientX: float
        clientY: float
        movementX: float
        movementY: float
        offsetX: float
        offsetY: float
        pageX: float
        pageY: float
        screenX: float
        screenY: float
        layerX: float
        layerY: float
        x: float
        y: float
        # -- keyboard -----------------------------------------------------
        key: str
        code: str
        char: str
        charCode: int
        keyCode: int
        location: int
        repeat: bool
        isComposing: bool
        altKey: bool
        ctrlKey: bool
        metaKey: bool
        shiftKey: bool
        # -- input / clipboard / wheel ------------------------------------
        data: str
        inputType: str
        dataTransfer: AsyncEventProxy[Any]
        clipboardData: AsyncEventProxy[Any]
        touches: list[Any]
        targetTouches: list[Any]
        changedTouches: list[Any]
        deltaX: float
        deltaY: float
        deltaZ: float
        deltaMode: int

        # -- methods ------------------------------------------------------
        # ``preventDefault()``, ``stopPropagation()``, ``stopImmediatePropagation()``
        # and ``resolve()`` are typed by the base classes. Only ``composedPath()``
        # differs, since it must be awaited here but not for a synchronous event.
        def composedPath(self) -> Awaitable[list[Any]]: ...


class SyncEvent(SyncEventProxy[_T]):
    """The event object handed to plain ``def`` event handlers

    Behaves like an :class:`AsyncEvent` except that reading something the snapshot does
    not already know about blocks until the browser answers. ReactPy runs these
    handlers in a worker thread so that blocking never stalls the event loop::

        def on_key_down(event: SyncEvent):
            if event.key == "Enter":
                event.target.focus()
    """

    if TYPE_CHECKING:
        # -- identity -----------------------------------------------------
        type: str
        target: SyncEventProxy[Any]
        currentTarget: SyncEventProxy[Any]
        srcElement: SyncEventProxy[Any]
        relatedTarget: SyncEventProxy[Any]
        view: SyncEventProxy[Any]
        # -- flags --------------------------------------------------------
        # ``defaultPrevented`` and ``propagationStopped`` are typed by the base class.
        bubbles: bool
        cancelable: bool
        composed: bool
        cancelBubble: bool
        isTrusted: bool
        eventPhase: int
        timeStamp: float
        returnValue: Any
        detail: Any
        # -- mouse --------------------------------------------------------
        button: int
        buttons: int
        clientX: float
        clientY: float
        movementX: float
        movementY: float
        offsetX: float
        offsetY: float
        pageX: float
        pageY: float
        screenX: float
        screenY: float
        layerX: float
        layerY: float
        x: float
        y: float
        # -- keyboard -----------------------------------------------------
        key: str
        code: str
        char: str
        charCode: int
        keyCode: int
        location: int
        repeat: bool
        isComposing: bool
        altKey: bool
        ctrlKey: bool
        metaKey: bool
        shiftKey: bool
        # -- input / clipboard / wheel ------------------------------------
        data: str
        inputType: str
        dataTransfer: SyncEventProxy[Any]
        clipboardData: SyncEventProxy[Any]
        touches: list[Any]
        targetTouches: list[Any]
        changedTouches: list[Any]
        deltaX: float
        deltaY: float
        deltaZ: float
        deltaMode: int

        # -- methods ------------------------------------------------------
        # ``preventDefault()``, ``stopPropagation()``, ``stopImmediatePropagation()``
        # and ``resolve()`` are typed by the base classes. Only ``composedPath()``
        # differs, since it blocks here rather than returning an awaitable.
        def composedPath(self) -> list[Any]: ...


def event_marker_id(item: Any) -> str | None:
    """Return the live event identifier attached to event ``data``, if any"""
    if not isinstance(item, Mapping):
        return None
    marker = item.get(EVENT_MARKER_KEY)
    if isinstance(marker, str):
        return marker
    if isinstance(marker, Mapping):
        event_id = marker.get("id")
        return event_id if isinstance(event_id, str) else None
    return None


def build_event_args(
    data: Sequence[Any],
    backend: EventProxyBackend | None,
    prefer_async: bool = True,
) -> tuple[list[Any], bool | None]:
    """Turn the ``data`` of a ``layout-event`` message into handler arguments

    Items which the client marked as live become :class:`AsyncEvent` or
    :class:`SyncEvent` objects, everything else stays exactly as it was. The second
    element of the result is the flavour which was used, or :data:`None` when no live
    event was present.
    """
    from reactpy.types import Event

    args: list[Any] = []
    flavor: bool | None = None
    for item in data:
        event_id = event_marker_id(item)
        if event_id is not None and backend is not None and backend.available:
            snapshot = {
                key: value for key, value in item.items() if key != EVENT_MARKER_KEY
            }
            event_class = AsyncEvent if prefer_async else SyncEvent
            args.append(event_class(backend, event_id, snapshot=snapshot))
            flavor = prefer_async
        elif isinstance(item, dict):
            args.append(
                Event(
                    {
                        key: value
                        for key, value in item.items()
                        if key != EVENT_MARKER_KEY
                    }
                )
            )
        else:
            args.append(item)
    return args, flavor


class EventArguments(list):
    """The positional arguments a :class:`~reactpy.types.BaseEventHandler` is called with

    Whether data should be handed out in blocking or awaitable form is only known once
    the handler itself runs, and merged handlers may mix both. This list therefore
    remembers the raw event data so that :meth:`rebuild` can hand each handler
    arguments of the flavour it needs.
    """

    def __init__(
        self,
        data: Sequence[Any],
        backend: EventProxyBackend | None = None,
        prefer_async: bool = True,
    ) -> None:
        built, flavor = build_event_args(data, backend, prefer_async)
        super().__init__(built)
        self._reactpy_data = data
        self._reactpy_backend = backend
        self._reactpy_flavor = flavor

    def rebuild(self, prefer_async: bool) -> EventArguments:
        """Return arguments of the requested flavour (possibly this very list)"""
        if self._reactpy_flavor is None or self._reactpy_flavor is prefer_async:
            return self
        return EventArguments(self._reactpy_data, self._reactpy_backend, prefer_async)


def uses_sync_event_proxy(args: Sequence[Any]) -> bool:
    """Whether any of the given handler arguments blocks on the client"""
    return any(isinstance(arg, SyncEventProxy) for arg in args)
