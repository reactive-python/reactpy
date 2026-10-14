"""Client-backed ("live") proxies for browser events.

Nothing about the object behind an event is sent to the server when it is dispatched.
The client keeps the object alive and sends only an id::

    {
        "type": "layout-event",
        "target": "key-path:onClick",
        "data": [{"__reactpy_event__": {"id": "5b1c..."}, "type": "click"}],
        "seq": 3,
    }

ReactPy turns that into an :class:`Event`. Reading any property of it hands back
another :class:`EventProxy`, and *awaiting* that proxy is what asks the browser for the
value:

.. code-block:: python

    async def on_click(event: Event):
        value = await event.target.value  # one round trip
        await event.target.focus()  # one round trip

This is deliberately the same shape as JavaScript. ``event.target.value`` names the same
property chain in both places; the only difference is that reading it from Python is an
``await``, because the value lives in the browser rather than in this process. Every
proxy is awaitable, always - whether the value happens to be known already or not.

A read belongs to the moment it is awaited rather than to the event which woke the
handler. ``await event.target.value`` asks the browser what the element holds *now*,
just as the same expression would in JavaScript, so a handler which is still queued
behind another event's work sees whatever that element has become by then - not the
value which triggered it. This is the whole of the difference between reading live and
being handed a snapshot: nothing is remembered about the past, and a handler which must
act on the value as it stood when its own event fired should read it before anything
else is given the chance to change it.

Waiting costs a round trip, so two things keep the count down. A property which has been
read is cached against its event, so reading it again sends nothing. Properties which are
in flight at the same moment are sent together as one message:

.. code-block:: python

    value, key = await event.read("target.value", "key")
    value, key = await asyncio.gather(event.target.value, event.key)

Both cost a single round trip. Two ``await`` expressions written one after the other
cannot be batched, because the second is not known until the first has landed.

Resolution travels over the existing connection with two extra message types:

.. code-block:: json

    {"type": "event-proxy-request", "requestId": "...", "eventId": "...",
     "path": ["target", "value"], "call": false, "args": [], "reply": true,
     "maxDepth": 10}

    {"type": "event-proxy-response", "requestId": "...", "ok": true,
     "value": "hello", "error": null, "code": null}

Several requests travel as one ``{"type": "event-proxy-request", "requests": [...]}``
and are answered by one ``{"type": "event-proxy-response", "responses": [...]}``.

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

CACHE_LIMIT = 2048
"""How many resolved property values a single connection remembers before starting over
"""

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
        self._cache: dict[tuple[str, tuple[str, ...]], Any] = {}
        self._inflight: dict[
            tuple[str, tuple[str, ...]], tuple[str, Future | None]
        ] = {}
        self._outgoing: list[dict[str, Any]] = []
        self._flush_scheduled = False

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
        self._inflight.clear()
        self._outgoing.clear()
        self._flush_scheduled = False

    def handle_response(self, message: Mapping[str, Any]) -> bool:
        """Route a ``event-proxy-response`` message to whoever is waiting for it

        A message either answers one request or, when several went out together, carries
        a ``responses`` list answering each of them in turn.

        Returns :data:`True` if the message was meant for this backend.
        """
        if message.get("type") != EVENT_PROXY_RESPONSE_TYPE:
            return False

        responses = message.get("responses")
        if isinstance(responses, list):
            for entry in responses:
                if isinstance(entry, Mapping):
                    self._route(entry)
            return True

        self._route(message)
        return True

    def _route(self, message: Mapping[str, Any]) -> None:
        """Deliver one answer to the request which asked for it"""
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
            return

        if not future.done():
            future.set_result(
                {
                    "ok": bool(message.get("ok")),
                    "value": message.get("value"),
                    "error": message.get("error"),
                    "code": message.get("code"),
                }
            )

    async def resolve(
        self,
        event_id: str,
        path: Sequence[str | int],
        call: bool = False,
        args: Sequence[Any] = (),
    ) -> Any:
        """Resolve ``path`` against the client side event (awaited from the loop)

        Reads are remembered against the event, so asking for the same property twice
        sends one request. A request which is already in flight is shared rather than
        duplicated.
        """
        key = None if call else self._cache_key(event_id, path)
        if key is not None:
            if key in self._cache:
                return self._cache[key]
            shared = self._inflight.get(key)
            if shared is not None:
                payload = await self._await(*shared, event_id, path)
                return self._to_value(payload, event_id, path)

        request_id, future = self._enqueue(event_id, path, call, args, reply=True)
        if key is not None and future is not None:
            self._inflight[key] = (request_id, future)
        try:
            payload = await self._await(request_id, future, event_id, path)
        finally:
            # Whatever happened, nobody may keep waiting on a future which is already
            # done - on a timeout it has been cancelled, and leaving it here would hand
            # that cancellation to the next reader of this path instead of letting it
            # ask the browser again.
            if key is not None:
                self._inflight.pop(key, None)
        value = self._to_value(payload, event_id, path)
        if key is not None:
            self._remember(key, value)
        return value

    async def resolve_many(
        self, event_id: str, paths: Sequence[Sequence[str | int]]
    ) -> list[Any]:
        """Resolve several paths of one event in as few messages as possible

        Anything already cached is answered on the spot. Everything else is enqueued
        together, so it leaves the process as a single batched request.
        """
        values: list[Any] = [None] * len(paths)
        outstanding: list[
            tuple[int, tuple[str, tuple[str, ...]], tuple[str, Future | None]]
        ] = []
        ours: list[tuple[str, tuple[str, ...]]] = []
        for index, path in enumerate(paths):
            key = self._cache_key(event_id, path)
            if key in self._cache:
                values[index] = self._cache[key]
                continue
            shared = self._inflight.get(key)
            if shared is not None:
                outstanding.append((index, key, shared))
                continue
            entry = self._enqueue(event_id, path, False, (), True)
            self._inflight[key] = entry
            ours.append(key)
            outstanding.append((index, key, entry))

        try:
            payloads = await asyncio.gather(
                *(
                    self._await(request_id, future, event_id, paths[index])
                    for index, _, (request_id, future) in outstanding
                )
            )
        finally:
            for key in ours:
                self._inflight.pop(key, None)
        for (index, key, _), payload in zip(outstanding, payloads, strict=True):
            values[index] = self._to_value(payload, event_id, paths[index])
            self._remember(key, values[index])
        return values

    def notify(
        self,
        event_id: str,
        path: Sequence[str | int],
        args: Sequence[Any] = (),
    ) -> None:
        """Call a client side method without waiting for its result (best effort)"""
        try:
            self._enqueue(event_id, path, True, args, reply=False)
        except EventProxyError:
            logger.debug(
                f"Could not schedule live call to {list(path)!r} of {event_id!r}"
            )
            return

    # -- internals --------------------------------------------------------

    @staticmethod
    def _cache_key(
        event_id: str, path: Sequence[str | int]
    ) -> tuple[str, tuple[str, ...]]:
        return event_id, tuple(str(segment) for segment in path)

    def _remember(self, key: tuple[str, tuple[str, ...]], value: Any) -> None:
        if len(self._cache) >= CACHE_LIMIT:
            # Reading is meant to be cheap, not a place to accumulate memory
            self._cache.clear()
        self._cache[key] = value

    async def _await(
        self,
        request_id: str,
        future: Future | None,
        event_id: str,
        path: Sequence[str | int],
    ) -> dict[str, Any]:
        if future is None:  # nocov - only reply=False requests have no future
            return {"ok": True, "value": None, "error": None, "code": None}
        try:
            return await asyncio.wait_for(
                asyncio.wrap_future(future), REACTPY_EVENT_PROXY_TIMEOUT.current
            )
        except (TimeoutError, FuturesTimeoutError):
            self._handle_timeout(request_id, event_id, path)

    def _enqueue(
        self,
        event_id: str,
        path: Sequence[str | int],
        call: bool,
        args: Sequence[Any],
        reply: bool,
    ) -> tuple[str, Future | None]:
        """Queue one request to leave with whatever else is waiting, and await it"""
        request_id, message, future = self._begin(
            event_id, path, call, args, reply=reply
        )
        self._outgoing.append(message)
        self._schedule_flush()
        return request_id, future

    def _schedule_flush(self) -> None:
        """Send everything queued, once, at the end of the current pass round the loop"""
        loop = self._loop
        if loop is None or self._flush_scheduled:
            return
        self._flush_scheduled = True
        if threading.get_ident() == self._loop_thread_id:
            loop.call_soon(self._flush)
        else:
            loop.call_soon_threadsafe(self._flush)

    def _flush(self) -> None:
        self._flush_scheduled = False
        batch, self._outgoing = self._outgoing, []
        if not batch:
            return
        if self._loop is None or self._send is None:
            self._abandon(batch)
            return
        message = (
            batch[0]
            if len(batch) == 1
            else {"type": EVENT_PROXY_REQUEST_TYPE, "requests": batch}
        )
        task = self._loop.create_task(self._send_message(message))
        self._send_tasks.add(task)
        task.add_done_callback(self._send_tasks.discard)

    def _abandon(self, batch: Sequence[dict[str, Any]]) -> None:
        for message in batch:
            request_id = message.get("requestId")
            future = (
                self._pending.pop(request_id, None)
                if isinstance(request_id, str)
                else None
            )
            if future is not None and not future.done():
                future.set_exception(
                    EventProxyUnavailable("no sender is bound to this connection")
                )

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

    async def _send_message(self, message: dict[str, Any]) -> None:
        send = self._send
        if send is None:  # nocov - guarded by _flush
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
        return deserialize_value(payload.get("value"), event_id, self)


_NO_PROXY_BACKEND = EventProxyBackend()
"""A backend which is never bound to a connection, standing in for an unbacked event

Since it has no sender, ``available`` is :data:`False` and any attempt to resolve
something through it raises :class:`EventProxyUnavailable`.
"""


async def _immediate(value: Any) -> Any:
    """Answer an await without asking the browser anything

    Used by a proxy whose value the client already gave us - the event ``type`` - so
    that awaiting any proxy behaves the same whether or not it is already known.
    """
    return value


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
    return value  # nocov - json.dumps only accepts types already handled above


def deserialize_value(
    value: Any,
    event_id: str,
    backend: EventProxyBackend,
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
            child = EventProxy(
                backend=backend,
                event_id=str(reference.get("eventId", event_id)),
                path=tuple(reference.get("path", ())),
            )
            child._reactpy_callable = bool(reference.get("callable"))
            return child
        return {
            key: deserialize_value(item, event_id, backend, depth + 1)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [deserialize_value(item, event_id, backend, depth + 1) for item in value]

    return value


class EventProxy(Generic[_T]):
    """A live, lazily resolved view onto a browser object

    Nothing about the object is known until it is asked for. Reading any property hands
    back another proxy, and *awaiting* that proxy is what sends the request::

        async def on_input(event: Event):
            value = await event.target.value
            await event.target.focus()

    This is the same property chain the browser sees. The one difference is that reading
    it from Python is an ``await``, because the value lives over the connection. Every
    proxy is awaitable, whether or not its value happens to be known already - there is
    no second, non-awaitable kind of value to trip over.

    A property which has been read is cached against its event, and properties which are
    in flight at the same moment travel together as one message::

        value, key = await event.read("target.value", "key")

    A property the browser will not give - a blocked member, an object it has forgotten,
    a path which is not there - raises a subclass of :class:`EventProxyError`. Nothing is
    ever quietly answered with :data:`None`.
    """

    __slots__ = (
        "_reactpy_backend",
        "_reactpy_callable",
        "_reactpy_debounce",
        "_reactpy_event_id",
        "_reactpy_flags",
        "_reactpy_has_value",
        "_reactpy_known",
        "_reactpy_path",
        "_reactpy_value",
    )

    def __init__(
        self,
        *,
        backend: EventProxyBackend | None = None,
        event_id: str = "",
        path: Sequence[str | int] = (),
        flags: dict[str, bool] | None = None,
        value: Any = _MISSING,
        known: Mapping[str, Any] | None = None,
    ) -> None:
        self._reactpy_backend = backend if backend is not None else _NO_PROXY_BACKEND
        self._reactpy_event_id = event_id
        self._reactpy_path: tuple[str | int, ...] = tuple(path)
        self._reactpy_flags = {} if flags is None else flags
        self._reactpy_debounce: int | None = None
        self._reactpy_callable = False
        self._reactpy_has_value = value is not _MISSING
        self._reactpy_value = None if value is _MISSING else value
        self._reactpy_known = {} if known is None else dict(known)

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
    def is_known(self) -> bool:
        """Whether the value is already held here, so awaiting sends nothing"""
        return self._reactpy_has_value

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(event_id={self._reactpy_event_id!r}, "
            f"path={list(self._reactpy_path)!r})"
        )

    def __dir__(self) -> list[str]:
        return sorted({*dir(type(self)), *self._reactpy_known_members()})

    def _reactpy_known_members(self) -> list[str]:
        """Properties the client told us about when it dispatched the event"""
        return list(self._reactpy_known)

    # -- child access -----------------------------------------------------

    def _reactpy_make_child(
        self, segment: str | int, value: Any = _MISSING
    ) -> EventProxy[Any]:
        """A proxy one segment deeper, awaiting which reads it from the browser

        The value comes free in one case only: the client volunteered it when it
        dispatched the event (the event ``type``, which is small and needed to describe
        the event even after the object behind it has been forgotten). The child is
        awaitable either way - a known value just means awaiting it sends nothing.
        """
        if value is _MISSING and self._reactpy_known:
            value = self._reactpy_known.get(str(segment), _MISSING)
        return EventProxy(
            backend=self._reactpy_backend,
            event_id=self._reactpy_event_id,
            path=(*self._reactpy_path, segment),
            flags=self._reactpy_flags,
            value=value,
        )

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
            return backend.resolve(self._reactpy_event_id, path, call=True, args=args)
        backend.notify(self._reactpy_event_id, path, args)
        return None

    # -- event level conveniences -----------------------------------------

    def preventDefault(self) -> None:
        """Prevent the default action of the underlying DOM event

        The body of this method is empty on purpose. ReactPy reads the bytecode of your
        handler as it is created, and finding this call anywhere within it sets
        :attr:`~reactpy.types.BaseEventHandler.prevent_default` to :data:`True`. The
        browser is then asked to call ``preventDefault()`` itself, before the event is
        ever sent to the server. Writing ``@event(prevent_default=True)`` does exactly
        the same thing, but says so out loud.

        If the object behind this proxy is still alive, the JavaScript call is also
        scheduled on the client without being waited for. The browser has usually moved
        on by then, so depend on the handler flag when the action truly must not happen.
        """
        self._reactpy_flags["preventDefault"] = True
        self._reactpy_invoke("preventDefault")

    def stopPropagation(self) -> None:
        """Stop the underlying DOM event from propagating further up the tree

        Like :meth:`preventDefault`, calling this is detected in the bytecode of your
        handler and turned into
        :attr:`~reactpy.types.BaseEventHandler.stop_propagation` - the browser stops
        the event before it reaches the server. The call is additionally forwarded to a
        still-live event object, but is not waited for.
        """
        self._reactpy_flags["stopPropagation"] = True
        self._reactpy_invoke("stopPropagation")

    def stopImmediatePropagation(self) -> None:
        """Also stop any remaining listeners of the underlying DOM event

        Detected in the bytecode of your handler just like :meth:`stopPropagation`, and
        additionally forwarded to a still-live event object.
        """
        self._reactpy_flags["stopPropagation"] = True
        self._reactpy_flags["stopImmediatePropagation"] = True
        self._reactpy_invoke("stopImmediatePropagation")

    @property
    def defaultPrevented(self) -> bool:
        """Whether :meth:`preventDefault` has been asked for on this proxy

        This reports what Python has asked the browser to do, not what the browser
        settled on - read the live value with ``await event.defaultPrevented`` if the
        distinction matters.
        """
        return bool(self._reactpy_flags.get("preventDefault"))

    @property
    def propagationStopped(self) -> bool:
        """Whether :meth:`stopPropagation` has been asked for on this proxy"""
        return bool(self._reactpy_flags.get("stopPropagation"))

    @property
    def debounce(self) -> int | None:
        """Rate limit (in milliseconds) applied to server driven value updates"""
        return self._reactpy_debounce

    @debounce.setter
    def debounce(self, value: int | None) -> None:
        self._reactpy_debounce = value

    # -- property access ----------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_reactpy") or (
            name.startswith("__") and name.endswith("__")
        ):
            # Never resolve internals or interpreter lookups against the browser
            raise AttributeError(name)
        return self._reactpy_make_child(name)

    # Deliberately no __getitem__, __len__, __iter__ or __contains__: a proxy is not a
    # container, and there is nothing to enumerate about an object which still lives in
    # the browser. Define __getitem__ without __iter__ and ``x in event`` would fall
    # back to trying event[0], event[1], ... forever, since no index is ever missing.

    # -- resolution -------------------------------------------------------

    def _reactpy_resolve_path(self, call: bool, args: Sequence[Any]) -> Any:
        return self._reactpy_backend.resolve(
            self._reactpy_event_id,
            self._reactpy_path,
            call=call,
            args=args,
        )

    def _reactpy_call_method(self, name: str, args: Sequence[Any]) -> Any:
        path = (*self._reactpy_path, name)
        return self._reactpy_backend.resolve(
            self._reactpy_event_id, path, call=True, args=args
        )

    def composedPath(self) -> Awaitable[list[Any]]:
        """Return the event's path, read from the browser

        Await the result::

            async def on_click(event: Event):
                print(await event.composedPath())
        """
        return self._reactpy_call_method("composedPath", ())

    def resolve(self) -> Awaitable[_T]:
        """Fetch the value this proxy currently points at from the browser

        Awaiting the proxy itself does the same thing; this exists for the times when
        spelling out the round trip reads better.
        """
        return self._reactpy_resolve_path(False, ())

    async def read(self, *paths: str | Sequence[Any]) -> tuple[Any, ...]:
        """Read one or more properties in as few round trips as possible

        Each argument is a dotted path, or a sequence of segments, relative to this
        proxy; the result is a tuple of the same length. Whatever is already known is
        answered on the spot and the rest goes to the browser as one message::

            async def on_input(event: Event):
                value, key = await event.read("target.value", "key")

        Awaiting the proxies directly reads just as well and shares the same cache::

            value, key = await asyncio.gather(event.target.value, event.key)

        Values are fetched when the read is made rather than when the event fired, so a
        read made after other work has intervened reports what the browser holds at that
        moment. Whatever was read is cached, and a cached answer is not re-fetched.
        """
        if not paths:
            return ()
        segments = [self._reactpy_normalize_path(path) for path in paths]
        values: list[Any] = [None] * len(segments)
        wanted: list[list[str | int]] = []
        wanted_at: list[int] = []
        for index, item in enumerate(segments):
            if len(item) == 1 and item[0] in self._reactpy_known:
                # The client sent this with the event, so asking costs nothing
                values[index] = self._reactpy_known[item[0]]
            else:
                wanted.append([*self._reactpy_path, *item])
                wanted_at.append(index)
        if wanted:
            resolved = await self._reactpy_backend.resolve_many(
                self._reactpy_event_id, wanted
            )
            for index, value in zip(wanted_at, resolved, strict=True):
                values[index] = value
        return tuple(values)

    def __await__(self) -> Any:
        if self._reactpy_has_value:
            return _immediate(self._reactpy_value).__await__()
        return self._reactpy_resolve_path(False, ()).__await__()

    def __call__(self, *args: Any) -> Awaitable[Any]:
        """Call the client side method this proxy currently points at"""
        return self._reactpy_resolve_path(True, args)

    def __bool__(self) -> bool:
        return True


if TYPE_CHECKING:
    _ElementMembers = dict[str, Any]


class Event(EventProxy[_T]):
    """The event object handed to event handler functions

    Reading any property of it hands back a proxy, and awaiting that proxy asks the
    browser for the value::

        async def on_key_down(event: Event):
            if await event.key == "Enter":
                await event.target.focus()
                print(await event.target.value)

    This is the property chain the browser itself uses. The only difference is that a
    read from Python is an ``await``, because the value lives in the browser. There is
    no snapshot to be surprised by, and no value which is sometimes awaitable and
    sometimes not - every proxy is awaitable, always.

    Each read is a round trip, so reads which are in flight together travel together::

        value, key = await event.read("target.value", "key")

    A property the browser will not give - one which is blocked, or an object it has
    already forgotten - raises a subclass of :class:`EventProxyError`.

    Every member below is a best-effort hint for editors and type checkers. At runtime
    any property of any browser object can be read - unlisted ones simply resolve to
    :class:`EventProxy`.
    """

    if TYPE_CHECKING:
        # -- identity -----------------------------------------------------
        type: str
        target: EventProxy[Any]
        currentTarget: EventProxy[Any]
        srcElement: EventProxy[Any]
        relatedTarget: EventProxy[Any]
        view: EventProxy[Any]
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
        dataTransfer: EventProxy[Any]
        clipboardData: EventProxy[Any]
        touches: list[Any]
        targetTouches: list[Any]
        changedTouches: list[Any]
        deltaX: float
        deltaY: float
        deltaZ: float
        deltaMode: int

        # -- methods ------------------------------------------------------
        # ``preventDefault()``, ``stopPropagation()``, ``stopImmediatePropagation()``,
        # ``composedPath()``, ``resolve()`` and ``read()`` are all typed by
        # :class:`EventProxy`, and every one of them is awaited.


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
) -> list[Any]:
    """Turn the ``data`` of a ``layout-event`` message into handler arguments

    Items which the client marked as live become :class:`Event` objects which read from
    and call into the browser. Nothing about them is filled in here beyond what the
    client chose to send alongside the id - plain scalars only, which in practice means
    the event ``type``. Anything that was never an object is handed over as it arrived.
    """
    args: list[Any] = []
    for item in data:
        event_id = event_marker_id(item) if backend is not None else None
        if event_id is None:
            args.append(item)
            continue
        known = {
            key: value
            for key, value in item.items()
            if key != EVENT_MARKER_KEY and isinstance(value, str | int | float | bool)
        }
        args.append(Event(backend=backend, event_id=event_id, known=known))
    return args


class EventArguments(list):
    """The positional arguments a :class:`~reactpy.types.BaseEventHandler` is called with

    Every handler is a coroutine, so there is a single flavour of event data and these
    arguments can be handed straight to whichever handlers the event is routed to.
    """

    def __init__(
        self,
        data: Sequence[Any],
        backend: EventProxyBackend | None = None,
    ) -> None:
        super().__init__(build_event_args(data, backend))
