/**
 * Live ("event proxy") access to the objects which triggered a ReactPy event.
 *
 * Every object dispatched by a VDOM event handler is registered here, so the server
 * can reach back into whatever actually triggered the event. What the client sends
 * alongside the ``layout-event`` is the serializable half of that object plus an id:
 *
 * ```js
 * { type: "click", target: { tagName: "INPUT" }, __reactpy_event__: { id: "..." } }
 * ```
 *
 * The server can then walk that object property by property, and call its methods, by
 * sending ``event-proxy-request`` messages:
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
 * Only what is needed is serialized, which removes the fixed recursion depth that the
 * snapshot alone imposes, while keeping anything which could be used to break out of
 * the page (window, document, prototype, eval, ...) firmly out of reach.
 */

export const EVENT_PROXY_REQUEST_TYPE = "event-proxy-request";
export const EVENT_PROXY_RESPONSE_TYPE = "event-proxy-response";
export const EVENT_MARKER_KEY = "__reactpy_event__";
export const EVENT_REFERENCE_KEY = "__reactpy_ref__";

/** How many dispatched objects are kept around at most */
export const MAX_LIVE_OBJECTS = 100;
/** How long an object may sit unused before it is forgotten (ms) */
export const LIVE_OBJECT_TTL_MS = 60_000;
/** How many properties of a single object are handed over at most */
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
 * are what the snapshot the client sends up front is made of.
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
 * on the prototype - so the chain is walked the same way the snapshot serializer does.
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
 * Turn a live browser value into something JSON can carry.
 *
 * Anything which is too deep, too large, recursive, or simply not data (a function) is
 * replaced with a :data:`Reference` so the server can ask for it later.
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

  const nested = new Set(seen);
  nested.add(value);
  const next = (item: unknown, segment: string, at: number) =>
    serializeValue(item, eventId, [...path, segment], options, at, nested);

  if (value instanceof Date) return value.toISOString();
  if (value instanceof RegExp) return String(value);
  if (value instanceof Error)
    return {
      name: value.name,
      message: value.message,
      stack: value.stack ?? null,
    };

  if (Array.isArray(value))
    return value.map((item, index) => next(item, String(index), depth + 1));

  if (typeof value === "object" && Symbol.iterator in value) {
    // NodeList, FileList, Set, Map, ... all read better as a list
    const items: any[] = [];
    let index = 0;
    for (const item of value as Iterable<unknown>) {
      if (index >= MAX_PROPERTIES) break;
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

/**
 * Replace every reference in a serialized value with ``null``.
 *
 * ``serializeValue`` leans on references for whatever JSON cannot carry - a function,
 * a DOM node, something too deep or already seen. Those are only worth sending to a
 * server which can ask about them afterwards, which in turn needs the object to still
 * be held here. A snapshot taken for a handler which never asked for live access has
 * nothing behind it, so the references are emptied rather than handed over as
 * something nobody will ever be able to answer.
 */
export function dropReferences(value: any): any {
  if (Array.isArray(value)) return value.map(dropReferences);
  if (value === null || typeof value !== "object") return value;
  if (readReference(value)) return null;
  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, dropReferences(item)]),
  );
}

/**
 * Serialize an event for a handler which will not be reaching back into the page.
 *
 * The object is not registered, so dispatching it costs the page nothing to remember,
 * and the snapshot carries no references which could only be answered by a lookup that
 * would never succeed. The empty event id is never resolved against the registry.
 */
export function serializeSnapshot(value: any): any {
  return dropReferences(serializeValue(value, ""));
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
 * Entries are bounded in count and in age: an object which nobody has asked about for
 * a while, or which does not fit alongside the most recent ones, is forgotten. Every
 * value which leaves this registry goes through ``serializeValue``, so functions and
 * anything which could be used to escape the page never do.
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

  /** Drop objects which went unused for too long, or which no longer fit */
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

  /** Answer an incoming ``event-proxy-request``, replying unless told not to */
  handleMessage(message: EventProxyRequest): void {
    if (!message || message.type !== EVENT_PROXY_REQUEST_TYPE) return;
    const response = this.resolve(message);
    if (message.reply !== false) this.send(response);
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
