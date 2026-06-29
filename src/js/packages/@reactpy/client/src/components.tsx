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
  getInitialDebounce,
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

type UserInputTarget =
  | HTMLInputElement
  | HTMLSelectElement
  | HTMLTextAreaElement;

function trackUserInput(
  event: TargetedEvent<any>,
  setValue: (value: any) => void,
  lastUserValue: MutableRefObject<any>,
  lastChangeTime: MutableRefObject<number>,
  lastInputDebounce: MutableRefObject<number>,
  debounce: number,
): void {
  if (!event.target) {
    return;
  }

  const newValue = (event.target as UserInputTarget).value;
  setValue(newValue);
  lastUserValue.current = newValue;
  lastChangeTime.current = Date.now();
  lastInputDebounce.current = debounce;
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
  const [value, setValue] = useState(props.value);
  const lastUserValue = useRef(props.value);
  const lastChangeTime = useRef(0);
  // Seed the debounce window from the handlers themselves when possible,
  // otherwise fall back to the per-tagName built-in default (200 ms for
  // user-input tags, 0 ms elsewhere). This ensures the very first
  // server-driven update already respects the configured debounce.
  const lastInputDebounce = useRef(
    getInitialDebounce(props, getDefaultDebounceMs(model.tagName)),
  );
  const reconcileTimeout = useRef<number | null>(null);

  // honor changes to value from the client via props
  useEffect(() => {
    const reconcileValue = () => {
      // If the new prop value matches what we last sent, we are in sync.
      // If it differs, wait until the debounce window expires before applying it.
      const elapsed = Date.now() - lastChangeTime.current;
      if (
        props.value === lastUserValue.current ||
        elapsed >= lastInputDebounce.current
      ) {
        reconcileTimeout.current = null;
        setValue(props.value);
        return;
      }

      reconcileTimeout.current = window.setTimeout(
        reconcileValue,
        Math.max(0, lastInputDebounce.current - elapsed),
      );
    };

    reconcileValue();

    return () => {
      if (reconcileTimeout.current !== null) {
        window.clearTimeout(reconcileTimeout.current);
        reconcileTimeout.current = null;
      }
    };
  }, [props.value]);

  for (const [name, prop] of Object.entries(props)) {
    if (typeof prop !== "function") {
      continue;
    }

    const givenHandler = prop as TaggedEventHandler;
    if (!givenHandler[HANDLER_MARKER]) {
      continue;
    }

    const handlerDebounce = givenHandler[HANDLER_DEBOUNCE];
    const effectiveDebounce = isValidDebounce(handlerDebounce)
      ? handlerDebounce
      : getDefaultDebounceMs(model.tagName);

    const throttled = isValidDebounce(givenHandler[HANDLER_THROTTLE])
      ? throttleHandler(givenHandler, givenHandler[HANDLER_THROTTLE] as number)
      : givenHandler;

    props[name] = (event: TargetedEvent<any>) => {
      trackUserInput(
        event,
        setValue,
        lastUserValue,
        lastChangeTime,
        lastInputDebounce,
        effectiveDebounce,
      );
      throttled(event);
    };
  }

  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the client
  // providing the models instead of the client rendering them.
  return createElement(
    model.tagName,
    // overwrite
    { ...props, value },
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
