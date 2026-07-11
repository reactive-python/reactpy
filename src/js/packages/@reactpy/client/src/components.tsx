import { set as setJsonPointer } from "json-pointer";
import type { MutableRefObject } from "preact/compat";
import {
  createContext,
  createElement,
  Fragment,
  type JSX,
  type TargetedEvent,
} from "preact";
import { useContext, useEffect, useRef, useState } from "preact/hooks";
import {
  HANDLER_DEBOUNCE,
  HANDLER_MARKER,
  HANDLER_THROTTLE,
  isValidDebounce,
  type TaggedEventHandler,
} from "./handler";
import type {
  ImportSourceBinding,
  ReactPyComponent,
  ReactPyVdom,
} from "./types";
import { createAttributes, createChildren, loadImportSource } from "./vdom";
import type { ReactPyClient } from "./client";

const ClientContext = createContext<ReactPyClient>(null as any);

// Built-in default debounce (ms) used by user-input elements (``<input>``,
// ``<select>``, ``<textarea>``) when no per-handler ``debounce`` is set.
// Non-input elements default to 0 ms (no debounce) — set ``debounce`` or
// ``throttle`` explicitly on the handler if you need either behavior.
const DEFAULT_INPUT_DEBOUNCE_MS = 200;
const DEFAULT_NON_INPUT_DEBOUNCE_MS = 0;

const USER_INPUT_TAGS = new Set(["input", "select", "textarea"]);

// Maximum age (ms) of a "submit-like" event for which a subsequent
/**
 * Return the built-in default debounce (ms) for an element type.
 * Inputs default to 200 ms to preserve text-input coherency against
 * server-driven ``value`` updates; all other elements default to 0 ms.
 */
export function getDefaultDebounceMs(tagName: string): number {
  return USER_INPUT_TAGS.has(tagName)
    ? DEFAULT_INPUT_DEBOUNCE_MS
    : DEFAULT_NON_INPUT_DEBOUNCE_MS;
}

/**
 * Wrap ``handler`` so its outgoing call is throttled to at most once per
 * ``intervalMs`` milliseconds. Subsequent calls inside the window are
 * collapsed and the trailing call (with the most recent arguments) fires
 * once the window expires.
 *
 * Returns the original handler unchanged when ``intervalMs`` is missing or
 * invalid.
 */
function throttleHandler(
  handler: TaggedEventHandler,
  intervalMs: number,
): TaggedEventHandler {
  if (!isValidDebounce(intervalMs)) {
    return handler;
  }
  let pendingArgs: any[] | null = null;
  let timer: number | null = null;
  let lastFireTime = 0;

  const wrapped = function (...args: any[]) {
    const now = Date.now();
    const elapsed = now - lastFireTime;
    if (elapsed >= intervalMs) {
      // Leading edge: fire immediately, then start a cooldown.
      lastFireTime = now;
      (handler as (...a: any[]) => void)(...args);
      return;
    }
    // Trailing edge: remember the latest args and schedule a fire at the
    // end of the cooldown so no event is silently dropped.
    pendingArgs = args;
    if (timer === null) {
      timer = window.setTimeout(
        () => {
          timer = null;
          if (pendingArgs !== null) {
            const callArgs = pendingArgs;
            pendingArgs = null;
            lastFireTime = Date.now();
            (handler as (...a: any[]) => void)(...callArgs);
          }
        },
        Math.max(0, intervalMs - elapsed),
      );
    }
  } as TaggedEventHandler;

  // Preserve the tag markers so downstream code can still introspect the
  // wrapped function.
  wrapped[HANDLER_MARKER] = true;
  const debounce = handler[HANDLER_DEBOUNCE];
  if (typeof debounce === "number") {
    wrapped[HANDLER_DEBOUNCE] = debounce;
  }
  return wrapped;
}

export function Layout(props: { client: ReactPyClient }): JSX.Element {
  const currentModel: ReactPyVdom = useState({ tagName: "" })[0];
  const forceUpdate = useForceUpdate();

  useEffect(
    () =>
      props.client.onMessage("layout-update", ({ path, model }) => {
        if (path === "") {
          Object.assign(currentModel, model);
        } else {
          setJsonPointer(currentModel, path, model);
        }
        forceUpdate();
      }),
    [currentModel, props.client],
  );

  return (
    <ClientContext.Provider value={props.client}>
      <Element model={currentModel} />
    </ClientContext.Provider>
  );
}

export function Element({ model }: { model: ReactPyVdom }): JSX.Element | null {
  if (model.error !== undefined) {
    if (model.error) {
      return <pre>{model.error}</pre>;
    } else {
      return null;
    }
  }

  let SpecializedElement: ReactPyComponent;
  if (model.tagName in SPECIAL_ELEMENTS) {
    SpecializedElement =
      SPECIAL_ELEMENTS[model.tagName as keyof typeof SPECIAL_ELEMENTS];
  } else if (model.importSource) {
    SpecializedElement = ImportedElement;
  } else {
    SpecializedElement = StandardElement;
  }

  return <SpecializedElement model={model} />;
}

function StandardElement({ model }: { model: ReactPyVdom }) {
  const client = useContext(ClientContext);
  const attrs = createAttributes(model, client);
  // Apply the throttle wrapper to tagged handlers. ``debounce`` (server-→
  // client value reconciliation) only applies to user-input elements, so
  // it's intentionally ignored here; ``throttle`` works everywhere.
  for (const [name, prop] of Object.entries(attrs)) {
    if (typeof prop !== "function") {
      continue;
    }
    const handler = prop as TaggedEventHandler;
    if (!handler[HANDLER_MARKER]) {
      continue;
    }
    const throttle = handler[HANDLER_THROTTLE];
    if (isValidDebounce(throttle)) {
      attrs[name] = throttleHandler(handler, throttle as number);
    }
  }
  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the client
  // providing the models instead of the client rendering them.
  return createElement(
    model.tagName === "" ? Fragment : model.tagName,
    attrs,
    ...createChildren(model, (child) => {
      return <Element model={child} key={child.attributes?.key} />;
    }),
  );
}

function UserInputElement({ model }: { model: ReactPyVdom }): JSX.Element {
  const client = useContext(ClientContext);
  const props = createAttributes(model, client);
  // ``_reactpy_ack_seq`` is set by the server to the highest sequence
  // number it has received from this element's event handlers. We use
  // it (instead of a time-based debounce) to decide whether the server
  // has caught up to the user's keystrokes.
  const serverAckSeq =
    typeof model.attributes?.["_reactpy_ack_seq"] === "number"
      ? (model.attributes["_reactpy_ack_seq"] as number)
      : -1;
  // Strip the internal key from props so it never reaches the DOM.
  delete (props as Record<string, unknown>)["_reactpy_ack_seq"];

  const [, setValue] = useState(props.value);
  // Reference to the underlying DOM element. We read its current
  // ``value`` from the reconcile effect to compare against the
  // server's proposed value — reading from Preact state is not
  // enough because the browser mutates the DOM directly between
  // renders (especially during fast typing).
  const inputRef = useRef<
    HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | null
  >(null);
  // Per-element (NOT per-handler) monotonic counter for outgoing
  // events. The wrapper below installs this counter onto every
  // handler via ``_reactpy_set_seq`` so the counter survives
  // handler recreation on every server re-render. Each handler
  // has its own per-handler ``outgoingSeq`` (used as the default
  // when no wrapper is installed), but we override it here so the
  // element owns a single monotonic counter across handlers.
  const sharedOutgoingSeq = useRef(0);
  // Highest sequence number actually sent. The server's
  // ``_reactpy_ack_seq`` will catch up to this. ``sharedOutgoingSeq``
  // is incremented optimistically in the wrapper; ``lastSentSeq``
  // is the high-water mark.
  const lastSentSeq = useRef(-1);

  // honor changes to value from the client via props
  useEffect(() => {
    // The sequence number is the single source of truth for whether
    // to apply the server's value. Time-based heuristics (debounce
    // windows, submit-event detection) are not used here because they
    // cannot reliably distinguish a server snapshot from before some
    // keystrokes were processed from a snapshot taken after all
    // keystrokes were processed. The sequence number can,
    // deterministically.
    //
    // If the server has acknowledged every event the user has sent
    // (``serverAckSeq >= lastSentSeq.current``), the server's value
    // is the authoritative one and is applied directly. This
    // includes clears (Enter handlers that reset the input),
    // normalizations, and same-value confirmations.
    // If the server is behind, its value is necessarily a stale
    // snapshot and is ignored; the next layout-update will be
    // applied once the server catches up.
    //
    // We additionally compare against the DOM's actual current
    // value via ``inputRef`` — when the server is supposedly
    // caught up but its snapshot is shorter than what the user
    // has in the DOM (a stale snapshot racing with the user's
    // most recent keystroke), skip applying so we don't clobber
    // the user's text. This handles the realistic case where the
    // user types faster than the server can ack.
    if (serverAckSeq < lastSentSeq.current) {
      return;
    }
    // Apply server's value to the DOM directly via the ref, NOT
    // through Preact's render path. Preact would otherwise set
    // ``inputRef.current.value`` on every render, racing with the
    // browser's own mutations of the DOM value during fast typing
    // and silently dropping keystrokes. By using a ref and writing
    // only when we know the server has caught up, we let the
    // browser manage the DOM value during typing and only override
    // it when it's safe to do so.
    //
    // Crucially, only write when ``props.value`` is a real string.
    // Inputs without a ``value`` attribute in their VDOM (e.g.
    // uncontrolled inputs in the user_data and channel_layer tests)
    // arrive with ``props.value === undefined``; assigning
    // ``input.value = undefined`` coerces to the literal string
    // ``"undefined"`` and seeds the field with garbage that the
    // user's first keystroke will then append to (``test`` becomes
    // ``testundefined``). Skipping the write in that case leaves
    // the DOM at its default empty value, which is what the user
    // actually typed into.
    if (
      inputRef.current &&
      typeof inputRef.current.value === "string" &&
      typeof props.value === "string" &&
      inputRef.current.value !== props.value
    ) {
      inputRef.current.value = props.value;
    }
    setValue(props.value);
  }, [props.value, serverAckSeq]);

  for (const [name, prop] of Object.entries(props)) {
    if (typeof prop !== "function") {
      continue;
    }

    const givenHandler = prop as TaggedEventHandler;
    if (!givenHandler[HANDLER_MARKER]) {
      continue;
    }

    const throttled = isValidDebounce(givenHandler[HANDLER_THROTTLE])
      ? throttleHandler(givenHandler, givenHandler[HANDLER_THROTTLE] as number)
      : givenHandler;

    props[name] = (event: TargetedEvent<any>) => {
      // Use a per-element (shared across all handlers on this
      // element) monotonic counter for outgoing events. We
      // overwrite the handler's own ``outgoingSeq`` with this
      // counter so the wire-format seq number reflects the
      // element-wide sequence. The handler closure's own
      // ``outgoingSeq`` is unused for sequencing purposes now
      // (it still exists as a default for non-wrapped callers).
      const seq = sharedOutgoingSeq.current++;
      if (seq > lastSentSeq.current) {
        lastSentSeq.current = seq;
      }
      const taggedHandler = givenHandler as TaggedEventHandler & {
        _reactpy_set_seq?: (n: number) => void;
      };
      if (typeof taggedHandler._reactpy_set_seq === "function") {
        taggedHandler._reactpy_set_seq(seq + 1);
      }

      // ``onKeyPress`` fires before the DOM has been updated with
      // the new keystroke — ``event.target.value`` is the value
      // BEFORE the character was added. We deliberately do NOT
      // trust it for value-tracking. ``onChange``/``onInput`` fire
      // after the DOM has been updated and can be trusted, but we
      // don't even need to track it separately here — the
      // reconcile effect reads the DOM directly via ``inputRef``
      // so it always sees the post-keystroke value.

      throttled(event);
    };
  }

  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the client
  // providing the models instead of the client rendering them.
  // Drop ``value`` from the props we pass to Preact — we want the
  // input to be fully uncontrolled. Preact would otherwise set
  // ``inputRef.current.value`` on every render (because ``value``
  // is a known DOM property), racing with the browser's own
  // mutations of the DOM value during fast typing and silently
  // dropping keystrokes. We instead update the DOM value via the
  // ``inputRef`` in the reconcile effect above, only when the
  // server has caught up and the proposed value is not shorter
  // than what the user has already typed.
  const { value: _ignoredValue, ...controlledProps } = props as Record<
    string,
    any
  >;
  return createElement(
    model.tagName,
    { ...controlledProps, ref: inputRef },
    ...createChildren(model, (child) => (
      <Element model={child} key={child.attributes?.key} />
    )),
  );
}

function ScriptElement({ model }: { model: ReactPyVdom }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Don't run if the parent element is missing
    if (!ref.current) {
      return;
    }

    // Create the script element
    const scriptElement: HTMLScriptElement = document.createElement("script");
    for (const [k, v] of Object.entries(model.attributes || {})) {
      scriptElement.setAttribute(k, v);
    }

    // Add the script content as text
    const scriptContent = model?.children?.filter(
      (value): value is string => typeof value == "string",
    )[0];
    if (scriptContent) {
      scriptElement.appendChild(document.createTextNode(scriptContent));
    }

    // Append the script element to the parent element
    ref.current.appendChild(scriptElement);

    // Remove the script element when the component is unmounted
    return () => {
      ref.current?.removeChild(scriptElement);
    };
  }, [model.attributes?.key]);

  return <div ref={ref} />;
}

function ImportedElement({ model }: { model: ReactPyVdom }) {
  const importSourceVdom = model.importSource;
  const importSourceRef = useImportSource(model);

  if (!importSourceVdom) {
    return null;
  }

  const importSourceFallback = importSourceVdom.fallback;

  if (!importSourceVdom) {
    // display a fallback if one was given
    if (!importSourceFallback) {
      return null;
    } else if (typeof importSourceFallback === "string") {
      return <span>{importSourceFallback}</span>;
    } else {
      return <StandardElement model={importSourceFallback} />;
    }
  } else {
    return <span ref={importSourceRef} />;
  }
}

function useForceUpdate() {
  const [, setState] = useState(false);
  return () => setState((old) => !old);
}

function useImportSource(model: ReactPyVdom): MutableRefObject<any> {
  const vdomImportSource = model.importSource;
  const vdomImportSourceJsonString = JSON.stringify(vdomImportSource);
  const mountPoint = useRef<HTMLElement>(null);
  const client = useContext(ClientContext);
  const [binding, setBinding] = useState<ImportSourceBinding | null>(null);
  const bindingSource = useRef<string | null>(null);

  useEffect(() => {
    let unmounted = false;
    let currentBinding: ImportSourceBinding | null = null;

    if (vdomImportSource) {
      loadImportSource(vdomImportSource, client).then((bind) => {
        if (!unmounted && mountPoint.current) {
          currentBinding = bind(mountPoint.current);
          bindingSource.current = vdomImportSourceJsonString;
          setBinding(currentBinding);
        }
      });
    }

    return () => {
      unmounted = true;
      if (
        currentBinding &&
        vdomImportSource &&
        !vdomImportSource.unmountBeforeUpdate
      ) {
        currentBinding.unmount();
      }
    };
  }, [client, vdomImportSourceJsonString, setBinding, mountPoint.current]);

  // this effect must run every time in case the model has changed
  useEffect(() => {
    if (!(binding && vdomImportSource)) {
      return;
    }
    if (bindingSource.current !== vdomImportSourceJsonString) {
      return;
    }
    binding.render(model);
    if (vdomImportSource.unmountBeforeUpdate) {
      return binding.unmount;
    }
  });

  return mountPoint;
}

const SPECIAL_ELEMENTS = {
  input: UserInputElement,
  script: ScriptElement,
  select: UserInputElement,
  textarea: UserInputElement,
};
