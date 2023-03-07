import React, {
  createElement,
  createContext,
  useState,
  useCallback,
  useRef,
  useContext,
  useEffect,
  Fragment,
  ComponentType,
  MutableRefObject,
  SyntheticEvent,
  ChangeEvent,
} from "react";
// @ts-ignore
import { set as setJsonPointer } from "json-pointer";
import { LayoutUpdateMessage } from "./messages";
import {
  ReactPyVdom,
  ReactPyComponent,
  createChildren,
  createAttributes,
  ReactPyVdomImportSource,
  loadImportSource,
  ImportSourceBinding,
} from "./reactpy-vdom";
import { ReactPyServer } from "./reactpy-server";

const LayoutServer = createContext<ReactPyServer>(null as any);

export function Layout(props: { server: ReactPyServer }): JSX.Element {
  const currentModel: ReactPyVdom = useState({ tagName: "" })[0];
  const forceUpdate = useForceUpdate();

  useEffect(() => {
    props.server
      .receiveMessage<LayoutUpdateMessage>("layout-update")
      .then(({ path, model }) => {
        setJsonPointer(currentModel, path, model);
        forceUpdate();
      });
  }, [currentModel, props.server]);

  return (
    <LayoutServer.Provider value={props.server}>
      <Element model={currentModel} />
    </LayoutServer.Provider>
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
  const server = React.useContext(LayoutServer);

  let type: string | ComponentType<any>;
  if (model.tagName == "") {
    type = Fragment;
  } else {
    type = model.tagName;
  }

  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the server
  // providing the models instead of the client rendering them.
  return createElement(
    type,
    createAttributes(model, server),
    ...createChildren(model, (model) => (
      <Element model={model} key={model.key} />
    )),
  );
}

function UserInputElement({ model }: { model: ReactPyVdom }): JSX.Element {
  const server = useContext(LayoutServer);
  const props = createAttributes(model, server);
  const [value, setValue] = React.useState(props.value);

  // honor changes to value from the server via props
  React.useEffect(() => setValue(props.value), [props.value]);

  const givenOnChange = props.onChange;
  if (typeof givenOnChange === "function") {
    props.onChange = (event: ChangeEvent<any>) => {
      // immediately update the value to give the user feedback
      setValue(event.target.value);
      // allow the server to respond (and possibly change the value)
      givenOnChange(event);
    };
  }

  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the server
  // providing the models instead of the client rendering them.
  return React.createElement(
    model.tagName,
    // overwrite
    { ...props, value },
    ...createChildren(model, (model) => (
      <Element model={model} key={model.key} />
    )),
  );
}

function ScriptElement({ model }: { model: ReactPyVdom }) {
  const ref = useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!ref.current) {
      return;
    }
    const scriptContent = model?.children?.filter(
      (value): value is string => typeof value == "string",
    )[0];

    let scriptElement: HTMLScriptElement;
    if (model.attributes) {
      scriptElement = document.createElement("script");
      for (const [k, v] of Object.entries(model.attributes)) {
        scriptElement.setAttribute(k, v);
      }
      if (scriptContent) {
        scriptElement.appendChild(document.createTextNode(scriptContent));
      }
      ref.current.appendChild(scriptElement);
    } else if (scriptContent) {
      let scriptResult = eval(scriptContent);
      if (typeof scriptResult == "function") {
        return scriptResult();
      }
    }
  }, [model.key, ref.current]);

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
      return <div>{importSourceFallback}</div>;
    } else {
      return <StandardElement model={importSourceFallback} />;
    }
  } else {
    return <div ref={importSourceRef} />;
  }
}

function useForceUpdate() {
  const [state, setState] = useState(false);
  return useCallback(() => setState(!state), []);
}

function useImportSource(model: ReactPyVdom): MutableRefObject<any> {
  const vdomImportSource = model.importSource;

  const mountPoint = useRef<HTMLElement>(null);
  const server = React.useContext(LayoutServer);
  const [binding, setBinding] = useState<ImportSourceBinding | null>(null);

  React.useEffect(() => {
    let unmounted = false;

    if (vdomImportSource) {
      loadImportSource(vdomImportSource, server).then((bind) => {
        if (!unmounted && mountPoint.current) {
          setBinding(bind(mountPoint.current));
        }
      });
    }

    return () => {
      unmounted = true;
      if (
        binding &&
        vdomImportSource &&
        !vdomImportSource.unmountBeforeUpdate
      ) {
        binding.unmount();
      }
    };
  }, [server, vdomImportSource, setBinding, mountPoint.current]);

  // this effect must run every time in case the model has changed
  useEffect(() => {
    if (!(binding && vdomImportSource)) {
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
