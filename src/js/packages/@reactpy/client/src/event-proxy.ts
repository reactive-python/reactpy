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
 * request for it is answered with a hard "not-found" error. The cap therefore has to
 * leave room for every event a single page can have in flight - a handler awaiting
 * several events, or a burst of keystrokes still being read - rather than merely being
 * small enough to be harmless.
 */
export const MAX_LIVE_OBJECTS = 512;
/** How long an object may sit unused before it is forgotten (ms) */
export const LIVE_OBJECT_TTL_MS = 60_000;
/** How many members of one object, list, or iterable are handed over at most */
export const MAX_PROPERTIES = 100;
/** How deep a single resolution may nest before references are used */
export const DEFAULT_MAX_DEPTH = 10;

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
  code?: "not-found" | "access" | null;
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
  maxDepth?: number;
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
  options: SerializeOptions = {},
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
  if (depth >= (options.maxDepth ?? DEFAULT_MAX_DEPTH))
    return reference(eventId, path);

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

/** Follow a full property path, refusing anything blocked along the way */
export function readPath(root: any, path: string[]): any {
  let node = root;
  for (const segment of path) node = readProperty(node, segment);
  return node;
}

function parentAndKey(root: any, path: string[]): { parent: any; key: string } {
  if (path.length === 0)
    throw new ProxyAccessError("an empty path cannot be resolved");
  let node = root;
  for (const segment of path.slice(0, -1)) node = readProperty(node, segment);
  return { parent: node, key: path[path.length - 1] };
}

type LiveObject = { value: any; added: number };

/**
 * Keeps the objects which recently triggered an event around so the server can walk
 * their properties and call their methods.
 *
 * This is the only place those objects exist as far as the server is concerned: nothing
 * about them is sent when the event is dispatched, so forgetting one is not a slowdown
 * but a dead end - every later request for it is answered with "not-found". Entries are
 * still bounded in count and in age, since a page cannot hold on to events forever.
 * Every value which leaves this registry goes through ``serializeValue``, so functions
 * and anything which could be used to escape the page never do.
 */
export class EventProxyRegistry {
  private readonly live = new Map<string, LiveObject>();
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

  /** Remember ``value`` and return the id the server will address it by */
  register(value: any): string {
    const eventId = `${this.clock().toString(36)}-${(this.nextId++).toString(36)}`;
    this.live.set(eventId, { value, added: this.clock() });
    this.prune();
    return eventId;
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
  }

  /**
   * Drop objects which went unused for too long, or which no longer fit
   *
   * Whatever is dropped here is gone for good as far as the server is concerned: the id
   * it holds keeps working, and keeps answering "not-found".
   */
  prune(): void {
    const now = this.clock();
    for (const [eventId, entry] of this.live) {
      if (now - entry.added > LIVE_OBJECT_TTL_MS) this.live.delete(eventId);
    }
    while (this.live.size > MAX_LIVE_OBJECTS) {
      const oldest = this.live.keys().next();
      if (oldest.done === true) break;
      this.live.delete(oldest.value);
    }
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
    for (const request of requests) {
      // Anything which is not a request at all cannot be answered meaningfully, so it
      // is passed over. Everything else is carried out; only the answering is optional.
      if (!request || typeof request !== "object") continue;
      const response = this.resolve(request);
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
    if (!entry)
      return reply(false, {
        error: `nothing is registered for event ${JSON.stringify(eventId)}`,
        code: "not-found",
      });

    // keep actively used objects around
    entry.added = this.clock();

    const path = Array.isArray(message.path) ? message.path.map(String) : [];
    const options: SerializeOptions = { maxDepth: message.maxDepth };

    try {
      if (message.call) {
        const value = this.call(eventId, entry.value, path, message.args || []);
        return reply(true, {
          value: serializeValue(value, eventId, path, options),
        });
      }
      if (path.length === 0)
        // the whole object the server is pointing at
        return reply(true, {
          value: serializeValue(entry.value, eventId, path, options),
        });

      const { parent, key } = parentAndKey(entry.value, path);
      const value = readProperty(parent, key);
      if (typeof value === "function")
        return reply(true, { value: reference(eventId, path, true) });
      return reply(true, {
        value: serializeValue(value, eventId, path, options),
      });
    } catch (error) {
      return reply(false, {
        error: error instanceof Error ? error.message : String(error),
        code: error instanceof ProxyNotFoundError ? "not-found" : "access",
      });
    }
  }

  private call(eventId: string, root: any, path: string[], args: any[]): any {
    if (path.length === 0)
      throw new ProxyAccessError("the event object itself cannot be called");
    const { parent, key } = parentAndKey(root, path);
    const method = readProperty(parent, key);
    if (typeof method !== "function")
      throw new ProxyAccessError(`${JSON.stringify(key)} is not a function`);
    return method.apply(
      parent,
      args.map((argument) => this.readArgument(argument)),
    );
  }

  private readArgument(argument: unknown): unknown {
    const ref = readReference(argument);
    if (ref) {
      const entry = this.live.get(ref.eventId);
      if (!entry)
        throw new ProxyNotFoundError(
          `nothing is registered for event ${JSON.stringify(ref.eventId)}`,
        );
      entry.added = this.clock();
      return readPath(entry.value, ref.path);
    }
    if (Array.isArray(argument))
      return argument.map((item) => this.readArgument(item));
    if (argument && typeof argument === "object") {
      const value: Record<string, unknown> = {};
      for (const [key, item] of Object.entries(argument))
        value[key] = this.readArgument(item);
      return value;
    }
    return argument;
  }
}
