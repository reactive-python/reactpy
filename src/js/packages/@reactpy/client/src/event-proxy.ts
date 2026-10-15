/**
 * Live ("event proxy") access to the objects which triggered a ReactPy event.
 *
 * Nothing about the object which triggered an event is sent to the server when the event
 * is dispatched. The client keeps the object alive here and puts only its id - plus the
 * event ``type``, the one plain value cheap enough to volunteer - into the
 * ``layout-event``:
 *
 * ```js
 * { type: "click", __reactpy_event__: { id: "..." } }
 * ```
 *
 * Everything else is read on demand. Each read is a round trip, so the server asks for
 * whatever it is missing as an ``event-proxy-request``:
 *
 * ```js
 * { type: "event-proxy-request", requestId: "...", eventId: "...",
 *   path: ["target", "value"], call: false, args: [], reply: true, maxDepth: 10 }
 * ```
 *
 * Values which cannot be turned into JSON come back as a reference which the server
 * turns into the next proxy:
 *
 * ```js
 * { __reactpy_ref__: { eventId: "...", path: ["target"], callable?: boolean } }
 * ```
 *
 * Requests which are outstanding at the same moment travel together as one message
 * carrying a ``requests`` list, and are answered by one message carrying the matching
 * ``responses`` list. A lone request keeps its unwrapped shape in both directions.
 *
 * Since there is no snapshot to fall back on, what keeps this safe is the blocklist
 * below: anything which could be used to break out of the page (window, document,
 * prototype, eval, ...) is refused on every read, whether it is asked for one property
 * at a time or handed over as part of a subtree.
 */

export const EVENT_PROXY_REQUEST_TYPE = "event-proxy-request";
export const EVENT_PROXY_RESPONSE_TYPE = "event-proxy-response";
export const EVENT_MARKER_KEY = "__reactpy_event__";
export const EVENT_REFERENCE_KEY = "__reactpy_ref__";

/**
 * How many dispatched objects are kept around at most.
 *
 * This is a correctness limit rather than a memory one. There is no snapshot left to
 * fall back on, so an object which has been evicted cannot be read again: every later
 * request for it is answered with a hard "evicted" error. The cap therefore has to
 * leave room for every event a single page can have in flight - a handler awaiting
 * several events, or a burst of keystrokes still being read - rather than merely being
 * small enough to be harmless.
 *
 * What goes when the cap is reached is the object the server has gone longest without
 * reading, not the one which happened to be dispatched first - see
 * {@link EventProxyRegistry.prune}.
 */
export const MAX_LIVE_OBJECTS = 512;
/**
 * How long an object the server never asked about may sit unused before it is forgotten.
 *
 * This is the rule for things nobody wanted: dispatched, never read once, and therefore
 * only taking up room. An object the server *has* read is exempt from it, because the
 * handler which read it may just be slow - {@link EventProxyRegistry.prune} says why, and
 * {@link MAX_LIVE_OBJECTS} is what actually bounds what the page holds.
 */
export const LIVE_OBJECT_TTL_MS = 60_000;
/** How many members of one object, list, or iterable are handed over at most */
export const MAX_PROPERTIES = 100;
/**
 * The deepest a request may ask the client to go, however it asks.
 *
 * ``maxDepth`` arrives from the server. A value which is negative, not a number at all,
 * or simply enormous would otherwise turn the bound which is there to protect the page
 * into the way past it, so it is read as a suggestion with a ceiling of its own.
 */
export const MAX_ALLOWED_DEPTH = 128;
/**
 * How many requests one batched message may carry out.
 *
 * The server queues whatever it wants to know during a pass round its loop, which is a
 * bounded number of things. A message carrying more than that did not come from a server
 * which means it, and carrying it out would be the page's one turn spent on nothing else.
 */
export const MAX_REQUESTS_PER_MESSAGE = 256;

/**
 * Read the depth a request asked for as a sane one, whatever it actually said
 *
 * ``maxDepth`` arrives from the server. A value which is negative, not a number at all,
 * or simply enormous would otherwise turn the bound which is there to protect the page
 * into the way past it, so it is read as a suggestion with a ceiling of its own.
 *
 * A request which did not say at all is answered with the shallowest thing there is: the
 * object as a single reference. Guessing a depth here would mean a malformed message
 * being handed more of the page than it asked for, whereas a reference costs the server
 * one more round trip and nothing else. The server in this repo always says.
 */
function allowedDepth(requested: unknown): number {
  if (typeof requested !== "number" || !Number.isFinite(requested)) return 0;
  return Math.min(Math.max(Math.floor(requested), 0), MAX_ALLOWED_DEPTH);
}

/**
 * Answer a request which is not going to be carried out
 *
 * Whatever wanted an answer gets one, because leaving it unanswered would have the
 * server sit there until its own timeout and count a client which is perfectly awake
 * against it.
 */
function refuse(request: EventProxyRequest, error: string): EventProxyResponse {
  return {
    type: EVENT_PROXY_RESPONSE_TYPE,
    requestId: typeof request.requestId === "string" ? request.requestId : "",
    ok: false,
    error,
    code: "access",
  };
}

export type EventProxyRequest = {
  type: typeof EVENT_PROXY_REQUEST_TYPE;
  requestId: string;
  eventId: string;
  path: string[];
  call: boolean;
  args: any[];
  reply: boolean;
  maxDepth?: number;
};

export type EventProxyResponse = {
  type: typeof EVENT_PROXY_RESPONSE_TYPE;
  requestId: string;
  ok: boolean;
  value?: any;
  error?: string | null;
  code?: "not-found" | "evicted" | "access" | null;
};

/**
 * Several requests sent as a single message, each shaped exactly like the one above.
 *
 * The server queues whatever it wants to know during a pass round its loop and sends it
 * all at once, so that a handler which reads a dozen properties pays for one round trip
 * instead of a dozen. Each entry keeps its own ``requestId``, and keeps the ``type`` of
 * the message it would have arrived in on its own.
 */
export type EventProxyRequestBatch = {
  type: typeof EVENT_PROXY_REQUEST_TYPE;
  requests: EventProxyRequest[];
};

/** The single message which answers a {@link EventProxyRequestBatch} */
export type EventProxyResponseBatch = {
  type: typeof EVENT_PROXY_RESPONSE_TYPE;
  responses: EventProxyResponse[];
};

export type EventMarker = {
  id: string;
};

/** Thrown when the object a request refers to is gone */
export class ProxyNotFoundError extends Error {}
/** Thrown when the requested property or method cannot be used */
export class ProxyAccessError extends Error {}
/**
 * Thrown when the object a request refers to was dropped to make room for another one
 *
 * Answers the same way {@link ProxyNotFoundError} does, but says something different about
 * why: the server had been handed this object and was still working with it when the page
 * ran out of room, rather than the object having gone stale on its own.
 */
export class ProxyEvictedError extends ProxyNotFoundError {}

/**
 * Properties which must never leave the page. Anything which could be used to reach
 * the wider document, walk a prototype chain, or evaluate code is refused. Ordinary
 * data properties (``value``, ``checked``, ``key``, ``className``, ...) are fine - they
 * are what a handler reads out of an event, one property per round trip.
 *
 * This is a security control, not a size control: with nothing sent up front, it is the
 * only thing standing between a request and the rest of the browser.
 */
const BLOCKED_MEMBERS = new Set<string>([
  // reaching the rest of the document, or the browser itself
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
  // reaching style sheets (which can carry same origin URLs)
  "ownerNode",
  "sheets",
  "styleSheet",
  // tree traversal - walk "composedPath()" or the snapshot instead
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
  // prototype and realm access
  "__proto__",
  "constructor",
  "prototype",
  "eval",
  "execScript",
  "Function",
  "setTimeout",
  "setInterval",
  "import",
]);

/** Returns true when ``name`` must not be read from a live object */
export function isBlockedMember(name: string): boolean {
  if (BLOCKED_MEMBERS.has(name)) return true;
  if (EVENT_MARKER_KEY === name || EVENT_REFERENCE_KEY === name) return true;
  // event handler attributes (``onclick``, ``onerror``, ...) are functions, and the
  // double underscore namespace belongs to whoever built the page
  if (/^on[a-z]/i.test(name)) return true;
  if (name.startsWith("__") && name.endsWith("__")) return true;
  return false;
}

export type Reference = {
  eventId: string;
  path: string[];
  callable?: boolean;
};

export type SerializeOptions = {
  /**
   * How deep to nest before handing back a reference instead of the value itself.
   *
   * Every caller states this. The registry takes it from the request which asked, via
   * :func:`allowedDepth`, and a caller with no request in front of it has to say for
   * itself - there is deliberately no depth to fall back on, since a bound nobody
   * chose is the same as a bound nobody meant.
   */
  maxDepth: number;
  maxProperties?: number;
};

/** Build the marker the server turns back into a proxy */
export function reference(
  eventId: string,
  path: string[],
  callable = false,
): Record<string, any> {
  const value: Record<string, any> = { eventId, path };
  if (callable) value.callable = true;
  return { [EVENT_REFERENCE_KEY]: value };
}

/** Read a reference handed to us by the server, if the given value is one */
export function readReference(value: unknown): Reference | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const raw = (value as Record<string, any>)[EVENT_REFERENCE_KEY];
  if (!raw || typeof raw !== "object" || typeof raw.eventId !== "string")
    return null;
  return {
    eventId: raw.eventId,
    path: Array.isArray(raw.path) ? raw.path.map(String) : [],
    callable: Boolean(raw.callable),
  };
}

/**
 * Collect the readable, non-function properties of ``value``.
 *
 * Own properties are not enough for DOM objects - nearly everything interesting lives
 * on the prototype - so the chain is walked the same way a property read on the page
 * would resolve it. Blocked names simply never make it into the result, and methods do
 * not either: those are called by an explicit path, not handed over as data.
 */
export function collectProperties(
  value: object,
  max: number = MAX_PROPERTIES,
): Record<string, unknown> {
  const collected: Record<string, unknown> = {};
  let count = 0;
  let prototype: any = value;
  while (prototype && prototype !== Object.prototype && count < max) {
    for (const name of Object.getOwnPropertyNames(prototype)) {
      if (Object.prototype.hasOwnProperty.call(collected, name)) continue;
      if (isBlockedMember(name)) continue;
      let property: unknown;
      try {
        property = (value as Record<string, any>)[name];
      } catch {
        continue; // getters which throw (detached nodes, revoked proxies, ...)
      }
      if (typeof property === "function") continue; // methods are called, not sent
      collected[name] = property;
      if (++count >= max) break;
    }
    prototype = Object.getPrototypeOf(prototype);
  }
  return collected;
}

/**
 * Turn a live browser value into the answer to a single on-demand read.
 *
 * Anything which is too deep, too large, recursive, or simply not data (a function) is
 * replaced with a :data:`Reference` so the server can ask about it separately - which is
 * exactly what a handler which reaches further down does.
 *
 * A list, or anything which iterates, hands over as many members as one object's
 * properties would and ends with a reference to itself when there were more than that,
 * so a handler can tell "that is all of it" from "there is more over there".
 */
export function serializeValue(
  value: unknown,
  eventId: string,
  path: string[] = [],
  options: SerializeOptions,
  depth = 0,
  seen: Set<unknown> = new Set(),
): any {
  if (value === null || value === undefined) return null;

  const kind = typeof value;
  if (kind === "string" || kind === "boolean") return value;
  if (kind === "number") return Number.isFinite(value) ? value : null;
  if (kind === "bigint") {
    const asNumber = Number(value);
    return Number.isSafeInteger(asNumber) ? asNumber : String(value);
  }
  if (kind === "symbol") return String(value);
  if (kind === "function") return reference(eventId, path, true);

  if (seen.has(value)) return reference(eventId, path);
  if (depth >= options.maxDepth) return reference(eventId, path);

  // A single "seen" set covers the whole answer rather than being copied per node. One
  // read reaches at most a bounded subtree of an object the server is already holding,
  // so anything met twice - a cycle, or a node shared between two properties - is better
  // handed back as a reference than expanded again.
  seen.add(value);
  const next = (item: unknown, segment: string, at: number) =>
    serializeValue(item, eventId, [...path, segment], options, at, seen);

  // One bound covers every kind of member collection - properties, list items, and the
  // items of anything which iterates - so that "how much arrives at once" is one
  // question with one answer.
  const maxMembers = options.maxProperties ?? MAX_PROPERTIES;

  if (value instanceof Date) return value.toISOString();
  if (value instanceof RegExp) return String(value);
  if (value instanceof Error)
    return {
      name: value.name,
      message: value.message,
      stack: value.stack ?? null,
    };

  if (Array.isArray(value)) {
    // A list is a collection of members like any other, so it is bounded the same way.
    // What did not fit is pointed at rather than dropped without a trace, which leaves
    // the server free to walk the rest one index at a time.
    const items: any[] = [];
    for (let index = 0; index < value.length && index < maxMembers; index++) {
      items.push(next(value[index], String(index), depth + 1));
    }
    if (items.length < value.length) items.push(reference(eventId, path));
    return items;
  }

  if (typeof value === "object" && Symbol.iterator in value) {
    // NodeList, FileList, Set, Map, ... all read better as a list
    const items: any[] = [];
    let index = 0;
    for (const item of value as Iterable<unknown>) {
      if (index >= maxMembers) {
        items.push(reference(eventId, path));
        break;
      }
      items.push(next(item, String(index), depth + 1));
      index++;
    }
    return items;
  }

  const properties = collectProperties(
    value as object,
    options.maxProperties ?? MAX_PROPERTIES,
  );
  const result: Record<string, unknown> = {};
  for (const name of Object.keys(properties)) {
    result[name] = next(properties[name], name, depth + 1);
  }
  return result;
}

/** Read a single property of a live object, refusing anything blocked */
export function readProperty(node: any, name: string): any {
  if (isBlockedMember(name))
    throw new ProxyAccessError(`reading "${name}" is not allowed`);
  if (node === null || node === undefined)
    throw new ProxyNotFoundError(`cannot read "${name}" of nothing`);
  if (typeof node === "string") {
    if (name === "length") return node.length;
    if (/^\d+$/.test(name)) return node[Number(name)] ?? null;
    throw new ProxyNotFoundError(`cannot read "${name}" of a string`);
  }
  if (typeof node !== "object" && typeof node !== "function")
    throw new ProxyNotFoundError(`cannot read "${name}" of a ${typeof node}`);
  if (!(name in node)) throw new ProxyNotFoundError(`"${name}" does not exist`);
  try {
    return node[name];
  } catch (error) {
    throw new ProxyAccessError(
      `reading "${name}" failed: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

/**
 * Follow a full property path, refusing anything blocked along the way.
 *
 * ``calls`` is what this object has already answered to for a method on it, which is
 * what lets a path leading through that method be resolved against the answer rather
 * than against the function itself.
 */
export function readPath(
  root: any,
  path: string[],
  calls?: ReadonlyMap<string, unknown>,
): any {
  let node = root;
  for (let index = 0; index < path.length; index++)
    node = stepDown(node, path, index, calls);
  return node;
}

function parentAndKey(
  root: any,
  path: string[],
  calls?: ReadonlyMap<string, unknown>,
): { parent: any; key: string } {
  if (path.length === 0)
    throw new ProxyAccessError("an empty path cannot be resolved");
  let node = root;
  for (let index = 0; index < path.length - 1; index++)
    node = stepDown(node, path, index, calls);
  return { parent: node, key: path[path.length - 1] };
}

type LiveObject = {
  value: any;
  /** When this object last mattered - dispatched, or answered a request about */
  added: number;
  /**
   * Whether the server has ever been answered about this object
   *
   * It decides which of the two ways an entry can end applies to it. An object which was
   * dispatched and never once read has nothing waiting on it, and goes the moment it goes
   * idle. An object the server has read belongs to a handler which may be part way through
   * awaiting something slow, and is only let go when it is genuinely in the way - see
   * {@link EventProxyRegistry.prune}.
   */
  asked: boolean;
  /**
   * What each path called on this object answered with, most recent last.
   *
   * A reference which came back from inside the result of a call names a place inside
   * that result, and the result is the only thing it can be resolved against. Keeping
   * it is what makes such a path walkable; replaying the call is not an option, since a
   * method may have side effects and may not even be there any more.
   */
  calls: Map<string, unknown>;
};

/** How many call results one object keeps around to walk paths through */
export const MAX_CALL_RESULTS_PER_OBJECT = 16;

/** What a recorded call is filed under - its own path, and nothing else's */
function callKey(path: string[]): string {
  return JSON.stringify(path);
}

/** Keep what a call answered, so that a path which leads through it still resolves */
function rememberCall(entry: LiveObject, path: string[], value: unknown): void {
  if (
    value === null ||
    (typeof value !== "object" && typeof value !== "function")
  )
    return; // a primitive has nothing inside it to walk into
  entry.calls.set(callKey(path), value);
  while (entry.calls.size > MAX_CALL_RESULTS_PER_OBJECT) {
    const oldest = entry.calls.keys().next();
    if (oldest.done === true) break;
    entry.calls.delete(oldest.value);
  }
}

/**
 * Step one segment deeper into a live value.
 *
 * A path which leads through a method is stepped through what that method answered
 * instead, whenever the page has been asked to call it before: the reference the server
 * is holding came out of that answer, and asking the method again would be both a second
 * side effect and a different answer.
 */
function stepDown(
  node: any,
  path: string[],
  index: number,
  calls?: ReadonlyMap<string, unknown>,
): any {
  if (typeof node === "function" && calls) {
    const answer = calls.get(callKey(path.slice(0, index)));
    if (answer !== undefined) node = answer;
  }
  return readProperty(node, path[index]);
}

/**
 * Keeps the objects which recently triggered an event around so the server can walk
 * their properties and call their methods.
 *
 * This is the only place those objects exist as far as the server is concerned: nothing
 * about them is sent when the event is dispatched, so forgetting one is not a slowdown
 * but a dead end - every later request for it is answered with "not-found", or with
 * "evicted" when the server had been reading it and the page ran out of room. Entries are
 * bounded in count by {@link MAX_LIVE_OBJECTS}, dropping whatever the server has gone
 * longest without reading, and in age by {@link LIVE_OBJECT_TTL_MS} for the objects it
 * never asked about at all.
 * Whatever a method on one of them answered is kept alongside it, for as long as the
 * entry lasts and up to a small number of calls, because a reference which came out of
 * such an answer names a place inside it and has nowhere else to be resolved against.
 * Every value which leaves this registry goes through ``serializeValue``, so functions
 * and anything which could be used to escape the page never do.
 */
/** Why an entry which is no longer here stopped answering */
type DroppedReason = "expired" | "evicted";

export class EventProxyRegistry {
  private readonly live = new Map<string, LiveObject>();
  /**
   * Why an id which is no longer here stopped answering, for as many as there is room to
   * remember
   *
   * Both reasons mean the same thing to a handler - the object is not coming back - but
   * they say different things about why, and a log which cannot tell them apart cannot
   * tell "stale anyway" from "the page ran out of room under us".
   */
  private readonly dropped = new Map<string, DroppedReason>();
  /**
   * Which id each object being kept is addressed by
   *
   * Dispatching the same object twice is one thing happening twice, so the second dispatch
   * is answered with the id the server already holds rather than a second copy of the same
   * object - which is also what keeps the count bound spent on objects which actually
   * differ from each other. A WeakMap so that an object nobody else can reach is not held
   * alive by this registry alone.
   */
  private identities = new WeakMap<object, string>();
  private readonly send: (message: any) => void;
  private readonly clock: () => number;
  private nextId = 0;

  constructor(
    send: (message: any) => void,
    clock: () => number = () => Date.now(),
  ) {
    this.send = send;
    this.clock = clock;
  }

  /**
   * Remember ``value`` and return the id the server will address it by
   *
   * An object which is already being kept is not registered a second time - it is brought
   * back to the live end of the queue and given back under the id the server knows.
   */
  register(value: any): string {
    if (this.keyable(value)) {
      const known = this.identities.get(value);
      const entry = known === undefined ? undefined : this.live.get(known);
      if (known !== undefined && entry !== undefined) {
        this.touch(known, entry);
        return known;
      }
    }
    const eventId = `${this.clock().toString(36)}-${(this.nextId++).toString(36)}`;
    this.live.set(eventId, {
      value,
      added: this.clock(),
      asked: false,
      calls: new Map(),
    });
    if (this.keyable(value)) this.identities.set(value, eventId);
    // This registry's ids only ever count up, so a fresh one cannot be in there - but a
    // hand-built one should not inherit somebody else's history either.
    this.dropped.delete(eventId);
    this.prune();
    return eventId;
  }

  /** Whether ``value`` has an identity worth dedupe on (primitives do not) */
  private keyable(value: any): value is object {
    return (
      value !== null &&
      (typeof value === "object" || typeof value === "function")
    );
  }

  /** Whether anything is still known about the given id */
  has(eventId: string): boolean {
    return this.live.has(eventId);
  }

  /** How many objects are currently kept around */
  get size(): number {
    return this.live.size;
  }

  /** Forget every registered object */
  clear(): void {
    this.live.clear();
    this.dropped.clear();
    // A WeakMap can only be replaced, not emptied - and an id left in it would point at
    // nothing, which is exactly the difference between a reused object and a stale entry.
    this.identities = new WeakMap();
  }

  /**
   * Mark an object as used right now
   *
   * Deleting and re-inserting is what makes the cap a least-recently-used bound rather
   * than a queue: a Map hands back its keys in the order they went in, so whatever has
   * just been read goes to the back of the line and something the server has gone longest
   * without reading is what disappears when the registry is full. Without this an object
   * could be dropped while a handler was part way through reading it, purely because it
   * happened to have been dispatched early.
   */
  private touch(eventId: string, entry: LiveObject): void {
    entry.added = this.clock();
    this.live.delete(eventId);
    this.live.set(eventId, entry);
  }

  /**
   * Drop objects which went idle without ever being read, or which no longer fit
   *
   * Whatever is dropped here is gone for good as far as the server is concerned: the id it
   * holds keeps working, and keeps answering *why* - "not-found" for one which went stale
   * unread, "evicted" for one the server was still using. ``dropped`` is what remembers
   * which of the two it was.
   *
   * Two rules, each with a single job. Age takes what nobody asked about: dispatched, never
   * once read, and only taking up room. It deliberately leaves alone an object the server
   * *has* read, because the handler which read it may simply be part way through awaiting
   * something slow - sweeping that one at sixty seconds would have the request it makes
   * when it gets back answered "not-found", with the page looking like it went away on its
   * own when it was the sweep which did it.
   *
   * Count is what actually bounds the page, and takes whatever has gone longest unread - so
   * a handler which keeps reading one object keeps it, however many events arrive behind it.
   *
   * This runs whenever the registry is used, not only when something is added to it.
   * Objects are kept for the server's benefit, so a page which stops dispatching events
   * still lets go of the ones which have gone idle rather than holding them for their
   * whole idle time.
   */
  prune(): void {
    const now = this.clock();
    for (const [eventId, entry] of this.live) {
      if (!entry.asked && now - entry.added > LIVE_OBJECT_TTL_MS) {
        this.live.delete(eventId);
        this.note(eventId, "expired");
      }
    }
    while (this.live.size > MAX_LIVE_OBJECTS) {
      const oldest = this.live.keys().next();
      if (oldest.done === true) break;
      this.live.delete(oldest.value);
      this.note(oldest.value, "evicted");
    }
  }

  /** Remember why an id stopped answering, for as long as there is room to */
  private note(eventId: string, reason: DroppedReason): void {
    this.dropped.delete(eventId);
    this.dropped.set(eventId, reason);
    while (this.dropped.size > MAX_LIVE_OBJECTS) {
      const oldest = this.dropped.keys().next();
      if (oldest.done === true) break;
      this.dropped.delete(oldest.value);
    }
  }

  /**
   * Say why an id is not being answered, in a way the server can tell apart
   *
   * "evicted" is the one worth a look at the page rather than at the handler: the registry
   * ran out of room under a server which was still reading the object. Everything else -
   * never registered, or idle and never once read - is the ordinary "not-found".
   */
  private missing(eventId: string): {
    error: string;
    code: "not-found" | "evicted";
  } {
    if (this.dropped.get(eventId) === "evicted")
      return {
        error:
          `event ${JSON.stringify(eventId)} no longer fits - the page keeps at most ` +
          `${MAX_LIVE_OBJECTS} live event objects, and this one was dropped to make room`,
        code: "evicted",
      };
    return {
      error: `nothing is registered for event ${JSON.stringify(eventId)}`,
      code: "not-found",
    };
  }

  /**
   * Answer an incoming ``event-proxy-request``, replying unless told not to
   *
   * Requests which were outstanding at the same moment arrive together as one message
   * carrying a ``requests`` list. Such a batch is answered by exactly one message whose
   * ``responses`` list holds one entry per request which wanted an answer - and by no
   * message at all when none of them did. A request which arrived on its own keeps its
   * unwrapped shape in both directions, so the common single read stays one small
   * message instead of paying for a wrapper around it.
   */
  handleMessage(message: EventProxyRequest | EventProxyRequestBatch): void {
    if (!message || message.type !== EVENT_PROXY_REQUEST_TYPE) return;

    // The requests are carried out first, and only then is the registry swept. Carrying
    // one out is the proof that its object is wanted - it is what refreshes the entry the
    // request names - so sweeping beforehand used to delete the very object a message had
    // arrived to be asked about, and answer a handler which was still working that the
    // page had gone away on its own.
    //
    // Sweeping here at all is what keeps a quiet page honest: whatever is registered is
    // kept for the server's benefit and nobody else is coming to take it away, so the
    // moment the server talks to us again is the moment to notice which of them have gone
    // stale. Waiting for the next event to be dispatched would hold detached objects for
    // their whole idle time.
    try {
      this.answer(message);
    } finally {
      this.prune();
    }
  }

  /** Carry out the single request, or the batch of them, which arrived in ``message`` */
  private answer(message: EventProxyRequest | EventProxyRequestBatch): void {
    const requests = (message as EventProxyRequestBatch).requests;
    if (!Array.isArray(requests)) {
      const request = message as EventProxyRequest;
      // Resolved whether or not an answer is wanted: a request which does not want one
      // is usually a call whose only point was to run a method in the page.
      const response = this.resolve(request);
      if (request.reply !== false) this.send(response);
      return;
    }

    const responses: EventProxyResponse[] = [];
    for (let index = 0; index < requests.length; index++) {
      const request = requests[index];
      // Anything which is not a request at all cannot be answered meaningfully, so it
      // is passed over. Everything else is carried out; only the answering is optional.
      if (!request || typeof request !== "object") continue;
      // Past the bound the page stops taking requests apart and says so, rather than
      // spending its one turn on an arbitrarily large list of them.
      const response =
        index >= MAX_REQUESTS_PER_MESSAGE
          ? refuse(
              request,
              `a single message may not ask for more than ${MAX_REQUESTS_PER_MESSAGE} things at once`,
            )
          : this.resolve(request);
      if (request.reply !== false) responses.push(response);
    }
    if (responses.length > 0) {
      const answered: EventProxyResponseBatch = {
        type: EVENT_PROXY_RESPONSE_TYPE,
        responses,
      };
      this.send(answered);
    }
  }

  /** Resolve a single request into the response for it */
  resolve(message: EventProxyRequest): EventProxyResponse {
    const requestId =
      typeof message.requestId === "string" ? message.requestId : "";
    const reply = (
      ok: boolean,
      extra: Partial<EventProxyResponse> = {},
    ): EventProxyResponse => ({
      type: EVENT_PROXY_RESPONSE_TYPE,
      requestId,
      ok,
      error: null,
      code: null,
      ...extra,
    });

    const eventId = typeof message.eventId === "string" ? message.eventId : "";
    const entry = this.live.get(eventId);
    if (!entry) return reply(false, this.missing(eventId));

    // Carrying this out is what keeps the object around: it is now the most recently used
    // thing the page holds, and the server has demonstrably asked about it - which is also
    // what takes it out of the reach of the idle sweep.
    entry.asked = true;
    this.touch(eventId, entry);

    const path = Array.isArray(message.path) ? message.path.map(String) : [];
    const maxDepth = allowedDepth(message.maxDepth);
    const options: SerializeOptions = { maxDepth };

    try {
      if (message.call) {
        const value = this.call(
          eventId,
          entry.value,
          path,
          message.args || [],
          maxDepth,
          entry.calls,
        );
        // Whatever the server was handed may have come out of this value, so it has to
        // stay around or the path to it leads nowhere.
        rememberCall(entry, path, value);
        return reply(true, {
          value: serializeValue(value, eventId, path, options),
        });
      }
      if (path.length === 0)
        // the whole object the server is pointing at
        return reply(true, {
          value: serializeValue(entry.value, eventId, path, options),
        });

      const value = readPath(entry.value, path, entry.calls);
      if (typeof value === "function")
        return reply(true, { value: reference(eventId, path, true) });
      return reply(true, {
        value: serializeValue(value, eventId, path, options),
      });
    } catch (error) {
      return reply(false, {
        error: error instanceof Error ? error.message : String(error),
        code:
          error instanceof ProxyEvictedError
            ? "evicted"
            : error instanceof ProxyNotFoundError
              ? "not-found"
              : "access",
      });
    }
  }

  private call(
    eventId: string,
    root: any,
    path: string[],
    args: any[],
    maxDepth: number,
    calls?: ReadonlyMap<string, unknown>,
  ): any {
    if (path.length === 0)
      throw new ProxyAccessError("the event object itself cannot be called");
    const { parent, key } = parentAndKey(root, path, calls);
    const method = readProperty(parent, key);
    if (typeof method !== "function")
      throw new ProxyAccessError(`${JSON.stringify(key)} is not a function`);
    return method.apply(
      parent,
      args.map((argument) => this.readArgument(argument, maxDepth, 0)),
    );
  }

  /**
   * Turn one argument of a call into the value it stands for.
   *
   * The shape of an argument is the server's business, not the page's, so it is held to
   * the same bound as a read is: whatever nests deeper than the request itself asked for
   * is refused instead of walked into.
   */
  private readArgument(
    argument: unknown,
    maxDepth: number,
    depth: number,
  ): unknown {
    if (depth > maxDepth)
      throw new ProxyAccessError(
        `an argument was nested more deeply than ${maxDepth} levels`,
      );
    const ref = readReference(argument);
    if (ref) {
      const entry = this.live.get(ref.eventId);
      if (!entry) {
        const { error, code } = this.missing(ref.eventId);
        throw code === "evicted"
          ? new ProxyEvictedError(error)
          : new ProxyNotFoundError(error);
      }
      entry.asked = true;
      this.touch(ref.eventId, entry);
      return readPath(entry.value, ref.path, entry.calls);
    }
    if (Array.isArray(argument))
      return argument.map((item) =>
        this.readArgument(item, maxDepth, depth + 1),
      );
    if (argument && typeof argument === "object") {
      const value: Record<string, unknown> = {};
      for (const [key, item] of Object.entries(argument))
        value[key] = this.readArgument(item, maxDepth, depth + 1);
      return value;
    }
    return argument;
  }
}
