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

function Element({ model, key }) {
  if (model.importSource) {
    return html`<${ImportedElement} model=${model} />`;
  } else {
    return html`<${StandardElement} model=${model} />`;
  }
}

function StandardElement({ model }) {
  const config = react.useContext(LayoutConfigContext);
  const children = elementChildren(model.children);
  const attributes = elementAttributes(model, config.sendEvent);
  if (model.children && model.children.length) {
    return html`<${model.tagName} ...${attributes}>${children}<//>`;
  } else {
    return html`<${model.tagName} ...${attributes} />`;
  }
}

function ImportedElement({ model }) {
  const config = react.useContext(LayoutConfigContext);
  const sendEvent = config.sendEvent;
  const mountPoint = react.useRef(null);
  const fallback = model.importSource.fallback;
  const importSource = useConst(() =>
    loadFromImportSource(config, model.importSource)
  );

  react.useEffect(() => {
    if (fallback) {
      reactDOM.unmountComponentAtNode(mountPoint.current);
    }
  }, []);

  // this effect must run every time in case the model has changed
  react.useEffect(() => {
    importSource.then(({ createElement, renderElement }) => {
      renderElement(
        createElement(
          model.tagName,
          elementAttributes(model, config.sendEvent),
          model.children
        ),
        mountPoint.current
      );
    });
  });

  react.useEffect(
    () => () =>
      importSource.then(({ unmountElement }) =>
        unmountElement(mountPoint.current)
      ),
    []
  );

  if (!fallback) {
    return html`<div ref=${mountPoint} />`;
  } else if (typeof fallback == "string") {
    return html`<div ref=${mountPoint}>${fallback}</div>`;
  } else {
    return html`<div ref=${mountPoint}>
      <${StandardElement} model=${fallback} />
    </div>`;
  }
}

function elementChildren(modelChildren) {
  if (!modelChildren) {
    return [];
  } else {
    return modelChildren.map((child) => {
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

function loadFromImportSource(config, importSource) {
  return config
    .loadImportSource(importSource.source, importSource.sourceType)
    .then((module) => {
      if (
        typeof module.createElement == "function" &&
        typeof module.renderElement == "function" &&
        typeof module.unmountElement == "function"
      ) {
        return {
          createElement: (type, props) =>
            module.createElement(module[type], props),
          renderElement: module.renderElement,
          unmountElement: module.unmountElement,
        };
      } else {
        return {
          createElement: (type, props, children) =>
            react.createElement(
              module[type],
              props,
              ...elementChildren(children)
            ),
          renderElement: reactDOM.render,
          unmountElement: reactDOM.unmountComponentAtNode,
        };
      }
    });
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

function useConst(func) {
  const ref = react.useRef();

  if (!ref.current) {
    ref.current = func();
  }

  return ref.current;
}
