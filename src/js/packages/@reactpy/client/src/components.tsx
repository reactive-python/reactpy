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

/**
 * Wrap ``handler`` so its outgoing call is debounced by
 * ``delayMs`` milliseconds. The first call schedules a fire after
 * the delay; subsequent calls inside the window reset the timer and
 * pass their arguments to the trailing call. Only one call lands
 * on the wrapped handler per debounce window.
 *
 * Returns the original handler unchanged when ``delayMs`` is missing
 * or invalid, so callers can pass a 0 / negative value to opt out.
 *
 * Unlike ``throttleHandler`` (which fires on the leading edge),
 * this strictly trailing-edge debounce is the right semantics for
 * text inputs: the server only sees the final state after the user
 * pauses typing, which is exactly when the reconcile can safely apply
 * a server-side transformation (normalisation, validation, etc.).
 */
function debounceHandler(
  handler: TaggedEventHandler,
  delayMs: number,
): TaggedEventHandler {
  if (!isValidDebounce(delayMs) || delayMs === 0) {
    return handler;
  }
  let timer: number | null = null;
  let pendingArgs: any[] | null = null;

  const wrapped = function (...args: any[]) {
    pendingArgs = args;
    if (timer !== null) {
      window.clearTimeout(timer);
    }
    timer = window.setTimeout(() => {
      timer = null;
      if (pendingArgs !== null) {
        const callArgs = pendingArgs;
        pendingArgs = null;
        (handler as (...a: any[]) => void)(...callArgs);
      }
    }, delayMs);
  } as TaggedEventHandler;

  // Preserve the tag markers so downstream code can still introspect
  // the wrapped function.
  wrapped[HANDLER_MARKER] = true;
  if (typeof handler[HANDLER_THROTTLE] === "number") {
    wrapped[HANDLER_THROTTLE] = handler[HANDLER_THROTTLE];
  }
  if (typeof handler[HANDLER_DEBOUNCE] === "number") {
    wrapped[HANDLER_DEBOUNCE] = handler[HANDLER_DEBOUNCE];
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
  // Apply the throttle wrapper to tagged handlers. ``throttle`` works on
  // every element; ``debounce`` is intentionally only applied by
  // ``UserInputElement`` (the only place where coalescing keystrokes
  // is meaningful — click handlers don't benefit from trailing-edge
  // coalescing, and applying debounce here would just delay
  // non-input events for no reason).
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

    // Apply ``throttle`` and/or ``debounce`` wrappers when the
    // handler opts into them. Throttle fires on the leading edge
    // (good for click-style events); debounce fires on the
    // trailing edge (good for typing, where you want the server
    // to see only the final state after the user pauses). Both
    // are no-ops when the corresponding keyword is absent, which
    // is the common case — the per-element seq reconcile is
    // already responsible for input coherency, so we don't apply
    // a debounce by default.
    const handlerDebounce = givenHandler[HANDLER_DEBOUNCE];
    const handlerThrottle = givenHandler[HANDLER_THROTTLE];
    let wrapped: TaggedEventHandler = givenHandler;
    if (isValidDebounce(handlerThrottle)) {
      wrapped = throttleHandler(wrapped, handlerThrottle as number);
    }
    if (isValidDebounce(handlerDebounce)) {
      wrapped = debounceHandler(wrapped, handlerDebounce as number);
    }

    props[name] = (event: TargetedEvent<any>) => {
      // Use a per-element (shared across all handlers on this
      // element) monotonic counter for outgoing events. We
      // overwrite the handler's own ``outgoingSeq`` with this
      // counter so the wire-format seq number reflects the
      // element-wide sequence. The handler closure's own
      // ``outgoingSeq`` is unused for sequencing purposes now
      // (it still exists as a default for non-wrapped callers).
      //
      // Critically, we increment the seq counter and update
      // ``lastSentSeq`` on every *user* event, not on every
      // server dispatch. If the handler is wrapped in a
      // debounce that coalesces several events into one server
      // dispatch, ``lastSentSeq`` will be higher than the seq
      // actually sent to the server, which is fine — the seq
      // we sent is the LATEST user-typed value, which is the
      // one the server actually processed.
      const seq = sharedOutgoingSeq.current++;
      if (seq > lastSentSeq.current) {
        lastSentSeq.current = seq;
      }
      const taggedHandler = givenHandler as TaggedEventHandler & {
        _reactpy_set_seq?: (n: number) => void;
      };
      if (typeof taggedHandler._reactpy_set_seq === "function") {
        // Push the handler's internal counter past our seq so
        // the next (possibly debounced) dispatch uses a seq
        // number that matches what the user just typed, not
        // whatever stale value the handler closure happened
        // to have left over.
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

      wrapped(event);
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
  const controlledProps: Record<string, any> = {};
  for (const key of Object.keys(props as Record<string, any>)) {
    if (key !== "value") {
      controlledProps[key] = (props as Record<string, any>)[key];
    }
  }
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
