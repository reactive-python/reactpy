import * as react from "react";
import * as reactDOM from "react-dom";
import htm from "htm";

import serializeEvent from "./event-to-object";

import { applyPatchInplace, joinUrl } from "./utils";

const html = htm.bind(react.createElement);
const LayoutConfigContext = react.createContext({});

export function mountLayout(
  mountElement,
  saveUpdateHook,
  sendEvent,
  importSourceUrl
) {
  reactDOM.render(
    html`
      <${Layout}
        saveUpdateHook=${saveUpdateHook}
        sendEvent=${sendEvent}
        importSourceUrl=${importSourceUrl}
      />
    `,
    mountElement
  );
}

export default function Layout({ saveUpdateHook, sendEvent, importSourceUrl }) {
  const [model, patchModel] = useInplaceJsonPatch({});

  react.useEffect(() => saveUpdateHook(patchModel), [patchModel]);

  if (model.tagName) {
    return html`
      <${LayoutConfigContext.Provider}
        value=${{
          sendEvent: sendEvent,
          importSourceUrl: importSourceUrl,
        }}
      >
        <${Element} model=${model} />
      <//>
    `;
  } else {
    return html`<div />`;
  }
}

function Element({ model }) {
  if (model.importSource) {
    return html`<${ImportedElement} model=${model} />`;
  } else {
    return html`<${StandardElement} model=${model} />`;
  }
}

function ImportedElement({ model }) {
  const config = react.useContext(LayoutConfigContext);
  const mountPoint = react.useRef(null);

  react.useEffect(() => {
    const importSource = joinUrl(
      config.importSourceUrl,
      model.importSource.source
    );
    eval(`import("${importSource}")`).then((module) => {
      mountImportSource(mountPoint.current, module, model, config);
    });
  });
  return html`<div ref=${mountPoint} />`;
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
    Object.keys(model.eventHandlers).forEach((eventName) => {
      const eventSpec = model.eventHandlers[eventName];
      attributes[eventName] = eventHandler(sendEvent, eventSpec);
    });
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

function mountImportSource(element, module, model, config) {
  if (model.importSource.hasMount) {
    if (model.children) {
      console.error("Mount function does not support children");
    }
    module.mount(
      element,
      module[model.tagName],
      elementAttributes(model, config.sendEvent)
    );
  } else {
    reactDOM.render(
      react.createElement(
        module[model.tagName],
        elementAttributes(model, config.sendEvent),
        ...elementChildren(model)
      ),
      element
    );
  }
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
