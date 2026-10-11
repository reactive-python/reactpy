// Tests for the live "event proxy" boundary. Everything which leaves the page goes
// through one of these functions, so the interesting cases are the ones where a value
// must *not* be handed over.
import { test, expect } from "bun:test";
import {
  DEFAULT_MAX_DEPTH,
  EVENT_MARKER_KEY,
  EVENT_PROXY_REQUEST_TYPE,
  EVENT_PROXY_RESPONSE_TYPE,
  EVENT_REFERENCE_KEY,
  EventProxyRegistry,
  type EventProxyRequest,
  LIVE_OBJECT_TTL_MS,
  MAX_LIVE_OBJECTS,
  ProxyAccessError,
  ProxyNotFoundError,
  collectProperties,
  dropReferences,
  isBlockedMember,
  readPath,
  readProperty,
  readReference,
  reference,
  serializeSnapshot,
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

test("handleMessage only answers proxy requests, and only when asked", () => {
  const { registry, replies } = make_registry();
  const eventId = registry.register(make_event());

  registry.handleMessage({
    type: "layout-update",
    eventId,
  } as unknown as EventProxyRequest);
  registry.handleMessage(null as unknown as EventProxyRequest);
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

test("serializeSnapshot hands over data and nothing which needs asking about", () => {
  // A handler which never asked to reach back into the page gets the serializable half
  // of the event, and no handle which could only be answered by a lookup that would
  // fail - the object was never registered here in the first place.
  const loop: Record<string, unknown> = { type: "click", value: "typed" };
  loop["again"] = loop;

  expect(serializeSnapshot(loop)).toEqual({
    type: "click",
    value: "typed",
    again: null,
  });
});

test("dropReferences empties references and leaves data alone", () => {
  expect(
    dropReferences({
      a: 1,
      b: [2, reference("e", ["x"])],
      c: { d: null },
    }),
  ).toEqual({ a: 1, b: [2, null], c: { d: null } });
});
