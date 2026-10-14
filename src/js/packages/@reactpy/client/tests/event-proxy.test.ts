// Tests for the live "event proxy" boundary. Nothing about a dispatched object is sent
// to the server any more - it all goes out through these functions, one property at a
// time - so the interesting cases are the ones where a value must *not* be handed over,
// and the ones where the shape of a request or its answer is what the server depends on.
import { test, expect } from "bun:test";
import {
  DEFAULT_MAX_DEPTH,
  EVENT_MARKER_KEY,
  EVENT_PROXY_REQUEST_TYPE,
  EVENT_PROXY_RESPONSE_TYPE,
  EVENT_REFERENCE_KEY,
  EventProxyRegistry,
  type EventProxyRequest,
  type EventProxyRequestBatch,
  type EventProxyResponse,
  LIVE_OBJECT_TTL_MS,
  MAX_ALLOWED_DEPTH,
  MAX_CALL_RESULTS_PER_OBJECT,
  MAX_LIVE_OBJECTS,
  MAX_REQUESTS_PER_MESSAGE,
  ProxyAccessError,
  ProxyNotFoundError,
  collectProperties,
  isBlockedMember,
  readPath,
  readProperty,
  readReference,
  reference,
  serializeValue,
} from "../src/event-proxy";

test("refuses members which could reach the rest of the page", () => {
  for (const name of [
    "window",
    "document",
    "ownerDocument",
    "parentNode",
    "shadowRoot",
    "__proto__",
    "constructor",
    "prototype",
    "eval",
    "Function",
    "setTimeout",
    "localStorage",
  ]) {
    expect(isBlockedMember(name)).toBe(true);
  }
});

test("refuses dunders, event handlers, and our own marker keys", () => {
  expect(isBlockedMember("__something__")).toBe(true);
  expect(isBlockedMember("onclick")).toBe(true);
  expect(isBlockedMember("onPointerDown")).toBe(true);
  expect(isBlockedMember(EVENT_MARKER_KEY)).toBe(true);
  expect(isBlockedMember(EVENT_REFERENCE_KEY)).toBe(true);
});

test("allows ordinary data properties through", () => {
  for (const name of [
    "value",
    "checked",
    "key",
    "className",
    "tagName",
    "type",
    "dataset",
    "detail",
  ]) {
    expect(isBlockedMember(name)).toBe(false);
  }
});

test("the handler pattern over-blocks a few plain names", () => {
  // "on..." is reserved for event handler attributes, so anything which merely starts
  // with those two letters goes with them. Worth knowing about before adding a prop.
  expect(isBlockedMember("only")).toBe(true);
  expect(isBlockedMember("one")).toBe(true);
  expect(isBlockedMember("once")).toBe(true);
});

test("readProperty hands over plain properties", () => {
  expect(readProperty({ value: "typed" }, "value")).toBe("typed");
  expect(readProperty({ target: { value: 7 } }, "target").value).toBe(7);
});

test("readProperty refuses blocked members before anything else", () => {
  expect(() => readProperty({ window: {} }, "window")).toThrow(
    ProxyAccessError,
  );
  // the block is checked first, so even reading from nothing cannot leak
  expect(() => readProperty(null, "__proto__")).toThrow(ProxyAccessError);
});

test("readProperty reports missing properties and non-objects", () => {
  expect(() => readProperty({}, "value")).toThrow(ProxyNotFoundError);
  expect(() => readProperty(null, "value")).toThrow(ProxyNotFoundError);
  expect(() => readProperty(7, "value")).toThrow(ProxyNotFoundError);
});

test("readProperty reads through strings like an array", () => {
  expect(readProperty("typed", "length")).toBe(5);
  expect(readProperty("typed", "1")).toBe("y");
  expect(readProperty("typed", "9")).toBe(null);
  expect(() => readProperty("typed", "toUpperCase")).toThrow(
    ProxyNotFoundError,
  );
});

test("readProperty wraps a throwing getter", () => {
  const detached = {
    get nodeName(): string {
      throw new Error("node is detached");
    },
  };
  expect(() => readProperty(detached, "nodeName")).toThrow(ProxyAccessError);
});

test("readPath walks every segment and refuses blocked ones", () => {
  const event = { target: { form: { action: "/submit" } } };
  expect(readPath(event, ["target", "form", "action"])).toBe("/submit");
  expect(readPath(event, [])).toBe(event);
  expect(() => readPath(event, ["target", "form", "ownerDocument"])).toThrow(
    ProxyAccessError,
  );
});

test("references round-trip", () => {
  const marked = reference("evt-1", ["target", "value"], true);
  expect(marked).toEqual({
    [EVENT_REFERENCE_KEY]: {
      eventId: "evt-1",
      path: ["target", "value"],
      callable: true,
    },
  });
  expect(readReference(marked)).toEqual({
    eventId: "evt-1",
    path: ["target", "value"],
    callable: true,
  });
  expect(reference("evt-2", [])).toEqual({
    [EVENT_REFERENCE_KEY]: { eventId: "evt-2", path: [] },
  });
});

test("serializeValue keeps plain data as-is", () => {
  expect(serializeValue("typed", "e")).toBe("typed");
  expect(serializeValue(true, "e")).toBe(true);
  expect(serializeValue(7, "e")).toBe(7);
  expect(serializeValue(10n, "e")).toBe(10);
  expect(serializeValue(2n ** 100n, "e")).toBe(String(2n ** 100n));
  expect(serializeValue(Symbol("tag"), "e")).toBe("Symbol(tag)");
  expect(serializeValue(null, "e")).toBe(null);
  expect(serializeValue(undefined, "e")).toBe(null);
});

test("serializeValue drops numbers JSON cannot carry", () => {
  expect(serializeValue(Number.NaN, "e")).toBe(null);
  expect(serializeValue(Number.POSITIVE_INFINITY, "e")).toBe(null);
});

test("serializeValue renders well-known objects readably", () => {
  expect(serializeValue(new Date("2026-10-09T00:00:00.000Z"), "e")).toBe(
    "2026-10-09T00:00:00.000Z",
  );
  expect(serializeValue(/ab+c/g, "e")).toBe("/ab+c/g");
  expect(serializeValue(new TypeError("bad"), "e")).toEqual({
    name: "TypeError",
    message: "bad",
    stack: expect.any(String),
  });
});

test("serializeValue turns functions into callable references", () => {
  expect(serializeValue(() => 1, "e", ["preventDefault"])).toEqual({
    [EVENT_REFERENCE_KEY]: {
      eventId: "e",
      path: ["preventDefault"],
      callable: true,
    },
  });
});

test("serializeValue reads iterables as lists", () => {
  expect(serializeValue(new Set(["a", "b"]), "e")).toEqual(["a", "b"]);
  expect(serializeValue([1, [2, 3]], "e")).toEqual([1, [2, 3]]);
});

test("serializeValue bounds a list by the same member count as an object", () => {
  // A list used to be the one collection with no bound at all, so an event which
  // carried a long one handed the whole of it over in a single message - while an
  // object with a hundred and one properties did not.
  const long = Array.from({ length: 250 }, (_, index) => index);
  const serialized = serializeValue(long, "e", [], { maxProperties: 5 });

  expect(serialized).toHaveLength(6);
  expect(serialized.slice(0, 5)).toEqual([0, 1, 2, 3, 4]);
  expect(readReference(serialized[5])).toEqual({
    eventId: "e",
    path: [],
    callable: false,
  });
});

test("serializeValue says when an iterable had more members than it sent", () => {
  const things = new Set(
    Array.from({ length: 9 }, (_, index) => `item-${index}`),
  );
  const serialized = serializeValue(things, "e", ["things"], {
    maxProperties: 3,
  });

  expect(serialized.slice(0, 3)).toEqual(["item-0", "item-1", "item-2"]);
  expect(readReference(serialized[3])?.path).toEqual(["things"]);

  // What fits is just the list, with nothing tacked on the end of it
  expect(serializeValue(new Set(["a", "b"]), "e", ["few"])).toEqual(["a", "b"]);
});

test("serializeValue uses references for cycles and excess depth", () => {
  const loop: Record<string, unknown> = { name: "loop" };
  loop["loopInto"] = loop;
  expect(serializeValue(loop, "e")).toEqual({
    name: "loop",
    loopInto: { [EVENT_REFERENCE_KEY]: { eventId: "e", path: ["loopInto"] } },
  });

  const deep = { a: { b: { c: 1 } } };
  expect(serializeValue(deep, "e", [], { maxDepth: 1 })).toEqual({
    a: { [EVENT_REFERENCE_KEY]: { eventId: "e", path: ["a"] } },
  });
  expect(DEFAULT_MAX_DEPTH).toBeGreaterThan(1);
  expect(serializeValue(deep, "e")).toEqual({ a: { b: { c: 1 } } });
});

test("blocked properties are dropped rather than turned into references", () => {
  // A reference would be an invitation to ask again, so a name which is not allowed to
  // leave the page disappears from the serialized object entirely.
  const event = { type: "click", self: { window: {} }, value: 1 };
  expect(serializeValue(event, "e")).toEqual({ type: "click", value: 1 });
});

test("collectProperties walks the prototype chain", () => {
  class Target {
    value = "typed";
    get tagName() {
      return "INPUT";
    }
    get ownerDocument() {
      return {};
    }
    focus(): void {}
  }
  expect(collectProperties(new Target())).toEqual({
    value: "typed",
    tagName: "INPUT",
  });
});

test("collectProperties gives up on throwing getters and respects the cap", () => {
  const throwing = {
    fine: 1,
    get boom(): number {
      throw new Error("detached");
    },
  };
  expect(collectProperties(throwing)).toEqual({ fine: 1 });
  expect(Object.keys(collectProperties({ a: 1, b: 2, c: 3 }, 2))).toEqual([
    "a",
    "b",
  ]);
});

test("readReference ignores anything which is not one", () => {
  expect(readReference(null)).toBe(null);
  expect(readReference("nope")).toBe(null);
  expect(readReference(42)).toBe(null);
  expect(readReference([])).toBe(null);
  expect(readReference({ [EVENT_REFERENCE_KEY]: null })).toBe(null);
  expect(readReference({ [EVENT_REFERENCE_KEY]: { path: [] } })).toBe(null);
  // a path which is not a list is treated as empty rather than thrown at
  expect(
    readReference({ [EVENT_REFERENCE_KEY]: { eventId: "e", path: 3 } }),
  ).toEqual({
    eventId: "e",
    path: [],
    callable: false,
  });
});

function make_registry(now: { value: number } = { value: 0 }) {
  const replies: any[] = [];
  const registry = new EventProxyRegistry(
    (message) => replies.push(message),
    () => now.value,
  );
  return { registry, replies, now };
}

/** Build a request the way the server sends one, filling in the fields a test rarely cares about */
function request(
  fields: Partial<EventProxyRequest> &
    Pick<EventProxyRequest, "eventId" | "path">,
): EventProxyRequest {
  return {
    type: EVENT_PROXY_REQUEST_TYPE,
    requestId: "r1",
    call: false,
    args: [],
    reply: true,
    ...fields,
  };
}

/**
 * Build the one message the server sends when several reads were outstanding at the end
 * of a pass round its loop. Each entry keeps the shape it would have had alone.
 */
function batch(...requests: EventProxyRequest[]): EventProxyRequestBatch {
  return { type: EVENT_PROXY_REQUEST_TYPE, requests };
}

/** Index the entries of an answered batch by the request each one belongs to */
function responses_of(message: any): Record<string, EventProxyResponse> {
  return Object.fromEntries(
    (message.responses as EventProxyResponse[]).map((entry) => [
      entry.requestId,
      entry,
    ]),
  );
}

function make_event() {
  const calls: string[] = [];
  return {
    calls,
    type: "click",
    target: { value: "typed", tagName: "INPUT", ownerDocument: {} },
    preventDefault() {
      calls.push("preventDefault");
    },
  };
}

test("the registry remembers what it was given", () => {
  const { registry } = make_registry();
  const eventId = registry.register(make_event());
  expect(registry.has(eventId)).toBe(true);
  expect(registry.size).toBe(1);
  registry.clear();
  expect(registry.has(eventId)).toBe(false);
  expect(registry.size).toBe(0);
});

test("the registry forgets idle objects and those which no longer fit", () => {
  const { registry, now } = make_registry();
  const eventId = registry.register(make_event());
  registry.prune();
  expect(registry.has(eventId)).toBe(true);

  now.value = LIVE_OBJECT_TTL_MS + 1;
  registry.prune();
  expect(registry.has(eventId)).toBe(false);

  for (let index = 0; index <= MAX_LIVE_OBJECTS; index++) registry.register({});
  expect(registry.size).toBe(MAX_LIVE_OBJECTS);
});

test("reading keeps an object from aging out", () => {
  const { registry, now } = make_registry();
  const eventId = registry.register(make_event());
  now.value = LIVE_OBJECT_TTL_MS - 1;
  registry.resolve(
    request({ type: EVENT_PROXY_REQUEST_TYPE, eventId, path: [] }),
  );
  now.value = LIVE_OBJECT_TTL_MS + 1;
  registry.prune();
  expect(registry.size).toBe(1);
});

test("an unknown event id is reported as missing", () => {
  const { registry } = make_registry();
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "r1",
      eventId: "nope",
      path: [],
    }),
  );
  expect(response).toEqual({
    type: EVENT_PROXY_RESPONSE_TYPE,
    requestId: "r1",
    ok: false,
    error: 'nothing is registered for event "nope"',
    code: "not-found",
  });
});

test("an empty path reads the whole registered object", () => {
  const { registry } = make_registry();
  const eventId = registry.register(make_event());
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "r1",
      eventId,
      path: [],
    }),
  );
  expect(response.ok).toBe(true);
  expect(response.value.type).toBe("click");
  // blocked members are dropped on the way out, not handed back as references
  expect(response.value.target.ownerDocument).toBeUndefined();
  expect(Object.keys(response.value.target)).toEqual(["value", "tagName"]);
  // methods are absent from the whole-object view - collectProperties only gathers
  // data - they surface as callable references when addressed by an explicit path
  expect(response.value.preventDefault).toBeUndefined();
  expect(Object.keys(response.value).sort()).toEqual([
    "calls",
    "target",
    "type",
  ]);
});

test("a path which lands on a method yields a callable reference", () => {
  const { registry } = make_registry();
  const eventId = registry.register(make_event());
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "r4",
      eventId,
      path: ["preventDefault"],
    }),
  );
  expect(response.ok).toBe(true);
  expect(response.value).toEqual({
    [EVENT_REFERENCE_KEY]: {
      eventId,
      path: ["preventDefault"],
      callable: true,
    },
  });
});

test("a path reads a single property", () => {
  const { registry } = make_registry();
  const eventId = registry.register(make_event());
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "r2",
      eventId,
      path: ["target", "value"],
    }),
  );
  expect(response.ok).toBe(true);
  expect(response.value).toBe("typed");
});

test("blocked and missing paths fail with the right code", () => {
  const { registry } = make_registry();
  const eventId = registry.register(make_event());

  const blocked = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      eventId,
      path: ["target", "ownerDocument", "defaultView"],
    }),
  );
  expect(blocked.ok).toBe(false);
  expect(blocked.code).toBe("access");

  const missing = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      eventId,
      path: ["target", "nope"],
    }),
  );
  expect(missing.ok).toBe(false);
  expect(missing.code).toBe("not-found");
});

test("methods are called with the registered object as their receiver", () => {
  const { registry } = make_registry();
  const event = make_event();
  const eventId = registry.register(event);
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "r3",
      eventId,
      path: ["preventDefault"],
      call: true,
      args: [],
    }),
  );
  expect(response.ok).toBe(true);
  expect(event.calls).toEqual(["preventDefault"]);
});

test("calling refuses the event itself, non-functions, and blocked members", () => {
  const { registry } = make_registry();
  const eventId = registry.register(make_event());

  expect(
    registry.resolve(
      request({
        type: EVENT_PROXY_REQUEST_TYPE,
        eventId,
        path: [],
        call: true,
      }),
    ).code,
  ).toBe("access");

  expect(
    registry.resolve(
      request({
        type: EVENT_PROXY_REQUEST_TYPE,
        eventId,
        path: ["type"],
        call: true,
      }),
    ).code,
  ).toBe("access");

  expect(
    registry.resolve(
      request({
        type: EVENT_PROXY_REQUEST_TYPE,
        eventId,
        path: ["window"],
        call: true,
      }),
    ).code,
  ).toBe("access");
});

test("a path which leads through a call result is still walkable", () => {
  // What comes back out of a call is named by a path leading through it, and the only
  // thing such a path can be resolved against is the answer the page already gave. It
  // used to lead to a function with no such property, and answer "not-found" - leaving
  // the server holding a reference to something it could never reach.
  const { registry } = make_registry();
  const note: Record<string, unknown> = { text: "written by the browser" };
  note["about"] = note; // a cycle, which is handed over as a reference
  const eventId = registry.register({
    reveal() {
      return note;
    },
  });

  const called = registry.resolve(
    request({ requestId: "call", eventId, path: ["reveal"], call: true }),
  );
  expect(called.ok).toBe(true);
  expect(readReference(called.value["about"])).toEqual({
    eventId,
    path: ["reveal", "about"],
    callable: false,
  });

  const walked = registry.resolve(
    request({ requestId: "walk", eventId, path: ["reveal", "about", "text"] }),
  );
  expect(walked.ok).toBe(true);
  expect(walked.value).toBe("written by the browser");
});

test("walking through a call result does not run the method again", () => {
  // The answer is kept rather than the call being made again: a method may have side
  // effects, and by now it may not even be there.
  const { registry } = make_registry();
  let runs = 0;
  const eventId = registry.register({
    make() {
      runs++;
      return { deep: { value: 42 } };
    },
  });

  const called = registry.resolve(
    request({
      requestId: "call",
      eventId,
      path: ["make"],
      call: true,
      maxDepth: 1,
    }),
  );
  expect(runs).toBe(1);
  expect(readReference(called.value["deep"])?.path).toEqual(["make", "deep"]);

  const walked = registry.resolve(
    request({ requestId: "walk", eventId, path: ["make", "deep", "value"] }),
  );
  expect(walked.ok).toBe(true);
  expect(walked.value).toBe(42);
  expect(runs).toBe(1);
});

test("only the most recent call results are kept to walk through", () => {
  // Keeping results is what keeps a page's memory bounded, so the oldest make room for
  // the newest rather than being held for as long as the event itself is.
  const { registry } = make_registry();
  const methods: Record<string, () => unknown> = {};
  for (let index = 0; index <= MAX_CALL_RESULTS_PER_OBJECT; index++)
    methods[`item${index}`] = () => ({ at: index });
  const eventId = registry.register(methods);

  for (let index = 0; index <= MAX_CALL_RESULTS_PER_OBJECT; index++)
    registry.resolve(
      request({
        requestId: `call-${index}`,
        eventId,
        path: [`item${index}`],
        call: true,
      }),
    );

  const kept = registry.resolve(
    request({
      eventId,
      path: [`item${MAX_CALL_RESULTS_PER_OBJECT}`, "at"],
    }),
  );
  expect(kept.ok).toBe(true);
  expect(kept.value).toBe(MAX_CALL_RESULTS_PER_OBJECT);

  const forgotten = registry.resolve(
    request({ eventId, path: ["item0", "at"] }),
  );
  expect(forgotten.ok).toBe(false);
  expect(forgotten.code).toBe("not-found");
});

test("arguments which are references are resolved on the page", () => {
  const { registry } = make_registry();
  const received: unknown[] = [];
  const eventId = registry.register({
    remember(...args: unknown[]) {
      received.push(...args);
      return args.length;
    },
  });
  const otherId = registry.register({ target: { value: "typed" } });
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      eventId,
      path: ["remember"],
      call: true,
      args: [
        { [EVENT_REFERENCE_KEY]: { eventId: otherId, path: ["target"] } },
        ["plain", { [EVENT_REFERENCE_KEY]: { eventId: otherId, path: [] } }],
        5,
      ],
    }),
  );
  expect(response.value).toBe(3);
  expect(received[0]).toEqual({ value: "typed" });
  expect(received[1]).toEqual(["plain", { target: { value: "typed" } }]);
  expect(received[2]).toBe(5);
});

test("an argument reference to a forgotten object is an error", () => {
  const { registry } = make_registry();
  const eventId = registry.register({
    remember(...args: unknown[]) {
      return args.length;
    },
  });
  const response = registry.resolve(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      eventId,
      path: ["remember"],
      call: true,
      args: [{ [EVENT_REFERENCE_KEY]: { eventId: "gone", path: [] } }],
    }),
  );
  expect(response.ok).toBe(false);
  expect(response.code).toBe("not-found");
});

test("an argument nested past the depth the request asked for is refused", () => {
  // An argument is the server's shape rather than the page's. Reading is bounded; an
  // argument used to be walked however deep it happened to go.
  const { registry } = make_registry();
  const eventId = registry.register({
    remember(...args: unknown[]) {
      return args.length;
    },
  });

  const response = registry.resolve(
    request({
      eventId,
      path: ["remember"],
      call: true,
      args: [[[[["far"]]]]],
      maxDepth: 2,
    }),
  );

  expect(response.ok).toBe(false);
  expect(response.code).toBe("access");
  expect(response.error).toContain("nested more deeply than 2 levels");
});

test("a request cannot ask the page to recurse further than it is willing to", () => {
  // ``maxDepth`` comes from the server, so it is a suggestion rather than an order: a
  // number which is negative, not a number, or simply enormous has to leave the page
  // standing rather than burying it in a stack it cannot come back out of.
  const { registry } = make_registry();
  const eventId = registry.register({ deep: nest(MAX_ALLOWED_DEPTH + 20) });

  for (const asked of [Number.NaN, -1, 100000, "deep"]) {
    const response = registry.resolve(
      request({
        eventId,
        path: ["deep"],
        maxDepth: asked as unknown as number,
      }),
    );
    expect(response.ok).toBe(true);

    let node: any = response.value;
    let depth = 0;
    while (node && node[EVENT_REFERENCE_KEY] === undefined && node["next"]) {
      node = node["next"];
      depth++;
    }
    expect(depth).toBeLessThanOrEqual(MAX_ALLOWED_DEPTH);
    expect(readReference(node)).not.toBe(null);
  }
});

test("a message which asks for far too much at once is refused the excess", () => {
  // The server asks for what it wants to know during one pass round its loop, which is
  // a bounded number of things. Carrying out an arbitrarily long list would spend the
  // page's one turn on nothing else, and whatever was refused still gets an answer
  // rather than leaving the server to time out on a client which is wide awake.
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());
  const requests = Array.from(
    { length: MAX_REQUESTS_PER_MESSAGE + 3 },
    (_, i) => request({ requestId: `r${i}`, eventId, path: ["type"] }),
  );

  registry.handleMessage(batch(...requests));

  const answered = replies[0].responses as EventProxyResponse[];
  expect(answered).toHaveLength(MAX_REQUESTS_PER_MESSAGE + 3);
  expect(answered[MAX_REQUESTS_PER_MESSAGE - 1].ok).toBe(true);
  expect(answered[MAX_REQUESTS_PER_MESSAGE].ok).toBe(false);
  expect(answered[MAX_REQUESTS_PER_MESSAGE].code).toBe("access");
  expect(answered[MAX_REQUESTS_PER_MESSAGE].error).toContain("more than");
  expect(answered[MAX_REQUESTS_PER_MESSAGE].requestId).toBe(
    `r${MAX_REQUESTS_PER_MESSAGE}`,
  );
});

function nest(levels: number): Record<string, unknown> {
  const root: Record<string, unknown> = {};
  let node = root;
  for (let index = 0; index < levels; index++) {
    node["next"] = {};
    node = node["next"] as Record<string, unknown>;
  }
  return root;
}

test("handleMessage only answers proxy requests, and only when asked", () => {
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  registry.handleMessage({
    type: "layout-update",
    eventId,
  } as unknown as EventProxyRequest);
  registry.handleMessage(null as unknown as EventProxyRequest);
  // a batch which was never a proxy request is ignored as a whole
  registry.handleMessage({
    type: "layout-update",
    requests: [request({ eventId, path: ["type"] })],
  } as unknown as EventProxyRequestBatch);
  expect(replies).toEqual([]);

  registry.handleMessage(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "quiet",
      eventId,
      path: ["type"],
      reply: false,
    }),
  );
  expect(replies).toEqual([]);

  registry.handleMessage(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "loud",
      eventId,
      path: ["type"],
    }),
  );
  expect(replies).toHaveLength(1);
  expect(replies[0]).toEqual({
    type: EVENT_PROXY_RESPONSE_TYPE,
    requestId: "loud",
    ok: true,
    error: null,
    code: null,
    value: "click",
  });
});

test("one request is answered by one unbatched response", () => {
  // The wrapper is reserved for batches: wrapping the single read which most events
  // need would only add bytes to the common case.
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  registry.handleMessage(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "solo",
      eventId,
      path: ["target", "value"],
    }),
  );

  expect(replies).toHaveLength(1);
  expect(replies[0]).toEqual({
    type: EVENT_PROXY_RESPONSE_TYPE,
    requestId: "solo",
    ok: true,
    error: null,
    code: null,
    value: "typed",
  });
  expect(replies[0].responses).toBeUndefined();
});

test("a batch of requests is answered by exactly one message", () => {
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());
  const otherId = registry.register({ target: { value: "other" } });

  registry.handleMessage(
    batch(
      request({ requestId: "a", eventId, path: ["type"] }),
      request({ requestId: "b", eventId, path: ["target", "value"] }),
      request({ requestId: "c", eventId: otherId, path: ["target", "value"] }),
    ),
  );

  expect(replies).toHaveLength(1);
  const [message] = replies;
  expect(message.type).toBe(EVENT_PROXY_RESPONSE_TYPE);
  expect(message.requestId).toBeUndefined();
  expect(message.responses).toHaveLength(3);

  // one entry per request, each carrying its own identity and its own answer
  const answered = message.responses as EventProxyResponse[];
  expect(answered.map((entry) => entry.requestId)).toEqual(["a", "b", "c"]);
  expect(answered.map((entry) => entry.value)).toEqual([
    "click",
    "typed",
    "other",
  ]);
  for (const entry of answered) {
    expect(entry.type).toBe(EVENT_PROXY_RESPONSE_TYPE);
    expect(entry.ok).toBe(true);
    expect(entry.error).toBeNull();
    expect(entry.code).toBeNull();
  }
});

test("a batch whose requests all want no answer sends nothing at all", () => {
  const { registry, replies } = make_registry();
  const event = make_event();
  const eventId = registry.register(event);

  registry.handleMessage(
    batch(
      request({
        requestId: "quiet-1",
        eventId,
        path: ["preventDefault"],
        call: true,
        reply: false,
      }),
      request({
        requestId: "quiet-2",
        eventId,
        path: ["target", "value"],
        reply: false,
      }),
    ),
  );

  expect(replies).toEqual([]);
  // they were still carried out - a request which does not want an answer is usually a
  // call whose only point was to run a method in the page
  expect(event.calls).toEqual(["preventDefault"]);
});

test("an empty batch sends nothing", () => {
  const { registry, replies } = make_registry();
  registry.register(make_event());
  registry.handleMessage(batch());
  expect(replies).toEqual([]);
});

test("only the requests which asked are answered, in the order they came", () => {
  const { registry, replies } = make_registry();
  const event = make_event();
  const eventId = registry.register(event);

  registry.handleMessage(
    batch(
      request({ requestId: "loud-1", eventId, path: ["type"] }),
      request({
        requestId: "quiet",
        eventId,
        path: ["preventDefault"],
        call: true,
        reply: false,
      }),
      request({ requestId: "loud-2", eventId, path: ["target", "tagName"] }),
    ),
  );

  expect(replies).toHaveLength(1);
  const answered = replies[0].responses as EventProxyResponse[];
  expect(answered.map((entry) => entry.requestId)).toEqual([
    "loud-1",
    "loud-2",
  ]);
  expect(responses_of(replies[0])["loud-2"].value).toBe("INPUT");
  expect(event.calls).toEqual(["preventDefault"]);
});

test("a batch answers each request on its own, failures included", () => {
  // One request going wrong says nothing about the others: every entry carries its own
  // ok/error/code, and the server decides which of them to raise on.
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  registry.handleMessage(
    batch(
      request({ requestId: "fine", eventId, path: ["type"] }),
      request({ requestId: "blocked", eventId, path: ["ownerDocument"] }),
      request({ requestId: "missing", eventId, path: ["target", "nope"] }),
      request({
        requestId: "gone",
        eventId: "never-registered",
        path: ["type"],
      }),
    ),
  );

  expect(replies).toHaveLength(1);
  const answered = responses_of(replies[0]);
  expect(Object.keys(answered).sort()).toEqual([
    "blocked",
    "fine",
    "gone",
    "missing",
  ]);
  expect(answered["fine"].ok).toBe(true);
  expect(answered["fine"].value).toBe("click");
  expect(answered["fine"].code).toBeNull();
  expect(answered["blocked"].ok).toBe(false);
  expect(answered["blocked"].code).toBe("access");
  expect(answered["missing"].ok).toBe(false);
  expect(answered["missing"].code).toBe("not-found");
  expect(answered["gone"].ok).toBe(false);
  expect(answered["gone"].code).toBe("not-found");
  expect(answered["gone"].error).toContain("never-registered");
});

test("a batch which carries something which is not a request skips it", () => {
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  registry.handleMessage(
    batch(
      null as unknown as EventProxyRequest,
      "nonsense" as unknown as EventProxyRequest,
      request({ requestId: "ok", eventId, path: ["type"] }),
    ),
  );

  expect(replies).toHaveLength(1);
  const answered = replies[0].responses as EventProxyResponse[];
  expect(answered.map((entry) => entry.requestId)).toEqual(["ok"]);
});

test("the blocklist refuses the names which could reach the page", () => {
  // Nothing is sent up front any more, so these refusals are the only thing between a
  // request and the rest of the browser - whether the read is asked for on its own,
  // buried behind an ordinary property, or smuggled in as part of a batch.
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  for (const name of [
    "ownerDocument",
    "__proto__",
    "eval",
    "parentNode",
    "window",
  ]) {
    const alone = registry.resolve(
      request({ requestId: name, eventId, path: [name] }),
    );
    expect(alone.ok).toBe(false);
    expect(alone.code).toBe("access");
    expect(alone.value).toBeUndefined();

    const buried = registry.resolve(
      request({ requestId: name, eventId, path: ["target", name] }),
    );
    expect(buried.ok).toBe(false);
    expect(buried.code).toBe("access");

    registry.handleMessage(
      batch(request({ requestId: name, eventId, path: ["target", name] })),
    );
    const [entry] = replies[replies.length - 1].responses;
    expect(entry.requestId).toBe(name);
    expect(entry.ok).toBe(false);
    expect(entry.code).toBe("access");
  }

  // ordinary properties still come through, blocked names alongside them included
  const plain = registry.resolve(
    request({ requestId: "plain", eventId, path: ["target", "value"] }),
  );
  expect(plain.ok).toBe(true);
  expect(plain.value).toBe("typed");
});

test("an object evicted by the cap is answered as not-found", () => {
  // There is no snapshot left to fall back on, so an event which has been forgotten
  // cannot be read at all: the handler is told so rather than handed a stale copy.
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  for (let index = 0; index <= MAX_LIVE_OBJECTS; index++) registry.register({});
  expect(registry.has(eventId)).toBe(false);

  registry.handleMessage(
    batch(request({ requestId: "gone", eventId, path: ["type"] })),
  );

  expect(replies).toHaveLength(1);
  const [entry] = replies[0].responses;
  expect(entry).toEqual({
    type: EVENT_PROXY_RESPONSE_TYPE,
    requestId: "gone",
    ok: false,
    error: `nothing is registered for event ${JSON.stringify(eventId)}`,
    code: "not-found",
  });
});

test("an object which aged out is answered as not-found", () => {
  const { registry, replies, now } = make_registry();
  const eventId = registry.register(make_event());

  now.value = LIVE_OBJECT_TTL_MS + 1;
  registry.prune();

  registry.handleMessage(
    request({
      type: EVENT_PROXY_REQUEST_TYPE,
      requestId: "late",
      eventId,
      path: ["target", "value"],
    }),
  );

  expect(replies).toHaveLength(1);
  expect(replies[0].requestId).toBe("late");
  expect(replies[0].ok).toBe(false);
  expect(replies[0].code).toBe("not-found");
});

test("answering a request takes the idle objects out with it", () => {
  // Objects are registered for the server's benefit and nothing else is coming to take
  // them away, so a page which stops dispatching events used to hold every one of them
  // for their whole idle time - a detached node is no less detached for nobody having
  // asked about it in the last minute.
  const { registry, replies, now } = make_registry();
  const idle = registry.register(make_event());

  now.value = LIVE_OBJECT_TTL_MS - 1;
  const busy = registry.register(make_event());

  now.value = LIVE_OBJECT_TTL_MS + 5;
  registry.handleMessage(
    request({ requestId: "ask", eventId: busy, path: [] }),
  );

  expect(replies).toHaveLength(1);
  expect(replies[0].ok).toBe(true);
  expect(registry.has(idle)).toBe(
    false,
    "the idle one went while nobody watched",
  );
  expect(registry.has(busy)).toBe(true, "the one being read is not idle");
});

test("the cap leaves room for every event a busy page can have in flight", () => {
  const { registry } = make_registry();
  const ids: string[] = [];
  for (let index = 0; index < 500; index++)
    ids.push(registry.register(make_event()));

  // A burst of keystrokes is still being read long after the last one fired, and an
  // event evicted too early fails hard - so the cap is a correctness limit rather than
  // a memory one, and has to be comfortably larger than what a page keeps outstanding.
  expect(registry.size).toBe(500);
  expect(ids.every((id) => registry.has(id))).toBe(true);
});
