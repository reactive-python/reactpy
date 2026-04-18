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
import type {
  ImportSourceBinding,
  ReactPyComponent,
  ReactPyVdom,
} from "./types";
import { createAttributes, createChildren, loadImportSource } from "./vdom";
import type { ReactPyClient } from "./client";

const ClientContext = createContext<ReactPyClient>(null as any);

const DEFAULT_INPUT_DEBOUNCE = 200;

type ReactPyInputHandler = ((event: TargetedEvent<any>) => void) & {
  debounce?: number;
  isHandler?: boolean;
};

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
  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the client
  // providing the models instead of the client rendering them.
  return createElement(
    model.tagName === "" ? Fragment : model.tagName,
    createAttributes(model, client),
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
  const lastInputDebounce = useRef(DEFAULT_INPUT_DEBOUNCE);
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

    const givenHandler = prop as ReactPyInputHandler;
    if (!givenHandler.isHandler) {
      continue;
    }

    props[name] = (event: TargetedEvent<any>) => {
      trackUserInput(
        event,
        setValue,
        lastUserValue,
        lastChangeTime,
        lastInputDebounce,
        typeof givenHandler.debounce === "number"
          ? givenHandler.debounce
          : DEFAULT_INPUT_DEBOUNCE,
      );
      givenHandler(event);
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
