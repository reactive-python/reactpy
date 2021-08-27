import React from "react";
import ReactDOM from "react-dom";
import htm from "htm";

import serializeEvent from "./event-to-object.js";

import { useJsonPatchCallback } from "./utils.js";

const html = htm.bind(React.createElement);
export const LayoutConfigContext = React.createContext({
  sendEvent: undefined,
  loadImportSource: undefined,
});

export function Layout({ saveUpdateHook, sendEvent, loadImportSource }) {
  const [model, patchModel] = useJsonPatchCallback({});

  React.useEffect(() => saveUpdateHook(patchModel), [patchModel]);

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

export function Element({ model }) {
  if (model.importSource) {
    return html`<${ImportedElement} model=${model} />`;
  } else {
    return html`<${StandardElement} model=${model} />`;
  }
}

export function elementChildren(modelChildren) {
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

export function elementAttributes(model, sendEvent) {
  const attributes = Object.assign({}, model.attributes);

  if (model.eventHandlers) {
    for (const [eventName, eventSpec] of Object.entries(model.eventHandlers)) {
      attributes[eventName] = eventHandler(sendEvent, eventSpec);
    }
  }

  return attributes;
}

function StandardElement({ model }) {
  const config = React.useContext(LayoutConfigContext);
  const children = elementChildren(model.children);
  const attributes = elementAttributes(model, config.sendEvent);
  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the server
  // providing the models instead of the client rendering them.
  return React.createElement(model.tagName, attributes, ...children);
}

function ImportedElement({ model }) {
  const config = React.useContext(LayoutConfigContext);

  const importSourceFallback = model.importSource.fallback;
  const [importSource, setImportSource] = React.useState(null);

  if (!importSource) {
    // load the import source in the background
    loadImportSource(config, model.importSource).then(setImportSource);

    // display a fallback if one was given
    if (!importSourceFallback) {
      return html`<div />`;
    } else if (typeof importSourceFallback == "string") {
      return html`<div>${importSourceFallback}</div>`;
    } else {
      return html`<${StandardElement} model=${importSourceFallback} />`;
    }
  } else {
    return html`<${RenderImportedElement}
      model=${model}
      importSource=${importSource}
    />`;
  }
}

function RenderImportedElement({ model, importSource }) {
  const config = React.useContext(LayoutConfigContext);
  const mountPoint = React.useRef(null);
  const sourceBinding = React.useRef(null);

  React.useEffect(() => {
    sourceBinding.current = importSource.bind(mountPoint.current);
    if (!importSource.data.unmountBeforeUpdate) {
      return sourceBinding.current.unmount;
    }
  }, []);

  // this effect must run every time in case the model has changed
  React.useEffect(() => {
    sourceBinding.current.render(model);
    if (importSource.data.unmountBeforeUpdate) {
      return sourceBinding.current.unmount;
    }
  });

  return html`<div ref=${mountPoint} />`;
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
    sendEvent({
      data: data,
      target: eventSpec["target"],
    });
  };
}

function loadImportSource(config, importSource) {
  return config
    .loadImportSource(importSource.source, importSource.sourceType)
    .then((module) => {
      if (typeof module.bind == "function") {
        return {
          data: importSource,
          bind: (node) => {
            const shortImportSource = {
              source: importSource.source,
              sourceType: importSource.sourceType,
            };
            const binding = module.bind(node, config, shortImportSource);
            if (
              typeof binding.render == "function" &&
              typeof binding.unmount == "function"
            ) {
              return {
                render: (model) => {
                  binding.render(
                    module[model.tagName],
                    elementAttributes(model, config.sendEvent),
                    model.children
                  );
                },
                unmount: binding.unmount,
              };
            } else {
              console.error(
                `${importSource.source} returned an impropper binding`
              );
            }
          },
        };
      } else {
        console.error(
          `${importSource.source} did not export a function 'bind'`
        );
      }
    });
}
