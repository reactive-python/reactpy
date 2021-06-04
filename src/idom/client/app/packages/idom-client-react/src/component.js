import * as react from "react";
import * as reactDOM from "react-dom";
import htm from "htm";

import serializeEvent from "./event-to-object";

import { applyPatchInplace, joinUrl } from "./utils";

const html = htm.bind(react.createElement);
const LayoutConfigContext = react.createContext({
  sendEvent: undefined,
  loadImportSource: undefined,
});

export function Layout({ saveUpdateHook, sendEvent, loadImportSource }) {
  const [model, patchModel] = useInplaceJsonPatch({});

  react.useEffect(() => saveUpdateHook(patchModel), [patchModel]);

  if (model.tagName) {
    return html`
      <${LayoutConfigContext.Provider} value=${{ sendEvent, loadImportSource }}>
        <${Element} model=${model} />
      <//>
    `;
  } else {
    return html`<div />`;
  }
}

function Element({ model }) {
  if (model.importSource) {
    if (model.importSource.exportsMount) {
      return html`<${MountedImportSource} model=${model} />`;
    } else {
      return html`<${DynamicImportSource} model=${model} />`;
    }
  } else {
    return html`<${StandardElement} model=${model} />`;
  }
}

function StandardElement({ model }) {
  const config = react.useContext(LayoutConfigContext);
  const children = elementChildren(model);
  const attributes = elementAttributes(model, config.sendEvent);
  if (model.children && model.children.length) {
    return html`<${model.tagName} ...${attributes}>${children}<//>`;
  } else {
    return html`<${model.tagName} ...${attributes} />`;
  }
}

function MountedImportSource({ model }) {
  const config = react.useContext(LayoutConfigContext);
  const mountPoint = react.useRef(null);
  const fallback = model.importSource.fallback;

  react.useEffect(() => {
    const unmountPromise = loadImportSource(config, model).then((module) => {
      const element = mountPoint.current;
      const component = module[model.tagName];
      const props = elementAttributes(model, config.sendEvent);
      const children = model.children;

      let args;
      if (!children) {
        args = [element, component, props, config];
      } else {
        args = [element, component, props, config, children];
      }

      reactDOM.unmountComponentAtNode(element);
      return module.mount(...args);
    });
    return () => {
      unmountPromise.then((unmount) => (unmount ? unmount() : undefined));
    };
  }, [model, mountPoint, config]);

  return createImportSourceFallback(mountPoint, fallback);
}

function DynamicImportSource({ model }) {
  const config = react.useContext(LayoutConfigContext);
  const mountPoint = react.useRef(null);
  const fallback = model.importSource.fallback;

  react.useEffect(() => {
    console.log(elementAttributes(model, config.sendEvent));
    loadImportSource(config, model).then((module) => {
      reactDOM.render(
        react.createElement(
          module[model.tagName],
          elementAttributes(model, config.sendEvent),
          ...elementChildren(model)
        ),
        mountPoint.current
      );
    });
    return () => {
      reactDOM.unmountComponentAtNode(mountPoint.current);
    };
  }, [model, mountPoint]);

  return createImportSourceFallback(mountPoint, fallback);
}

function createImportSourceFallback(mountPointRef, fallback) {
  if (!fallback) {
    return html`<div ref=${mountPointRef} />`;
  } else if (typeof fallback == "string") {
    return html`<div ref=${mountPointRef}>${fallback}</div>`;
  } else {
    return html`<div ref=${mountPointRef}>
      <${StandardElement} model=${fallback} />
    </div>`;
  }
}

function elementChildren(model) {
  if (!model.children) {
    return [];
  } else {
    return model.children.map((child) => {
      switch (typeof child) {
        case "object":
          return html`<${Element} key=${child.key} model=${child} />`;
        case "string":
          return child;
      }
    });
  }
}

function elementAttributes(model, sendEvent) {
  const attributes = Object.assign({}, model.attributes);

  if (model.eventHandlers) {
    for (const [eventName, eventSpec] of Object.entries(model.eventHandlers)) {
      attributes[eventName] = eventHandler(sendEvent, eventSpec);
    }
  }

  return attributes;
}

function eventHandler(sendEvent, eventSpec) {
  return function () {
    const data = Array.from(arguments).map((value) => {
      if (typeof value === "object" && value.nativeEvent) {
        if (eventSpec["preventDefault"]) {
          value.preventDefault();
        }
        if (eventSpec["stopPropagation"]) {
          value.stopPropagation();
        }
        return serializeEvent(value);
      } else {
        return value;
      }
    });
    const sentEvent = new Promise((resolve, reject) => {
      const msg = {
        data: data,
        target: eventSpec["target"],
      };
      sendEvent(msg);
      resolve(msg);
    });
  };
}

function loadImportSource(config, model) {
  return config.loadImportSource(
    model.importSource.source,
    model.importSource.sourceType
  );
}

function useInplaceJsonPatch(doc) {
  const ref = react.useRef(doc);
  const forceUpdate = useForceUpdate();

  const applyPatch = react.useCallback(
    (path, patch) => {
      applyPatchInplace(ref.current, path, patch);
      forceUpdate();
    },
    [ref, forceUpdate]
  );

  return [ref.current, applyPatch];
}

function useForceUpdate() {
  const [, updateState] = react.useState();
  return react.useCallback(() => updateState({}), []);
}
