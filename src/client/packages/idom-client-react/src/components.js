import React from "react";
import ReactDOM from "react-dom";
import htm from "htm";

import { useJsonPatchCallback } from "./json-patch.js";
import { loadModelImportSource } from "./import-source.js";
import {
  createElementAttributes,
  createElementChildren,
} from "./element-utils.js";

const html = htm.bind(React.createElement);
export const LayoutContext = React.createContext({
  sendEvent: undefined,
  loadImportSource: undefined,
});

export function Layout({ saveUpdateHook, sendEvent, loadImportSource }) {
  const [model, patchModel] = useJsonPatchCallback({});

  React.useEffect(() => saveUpdateHook(patchModel), [patchModel]);

  return html`
    <${LayoutContext.Provider} value=${{ sendEvent, loadImportSource }}>
      <${Element} model=${model} />
    <//>
  `;
}

export function Element({ model }) {
  if (!model.tagName) {
    if (model.error) {
      return html`<pre>${model.error}</pre>`;
    } else {
      return null;
    }
  } else if (model.importSource) {
    return html`<${ImportedElement} model=${model} />`;
  } else {
    return html`<${StandardElement} model=${model} />`;
  }
}

function StandardElement({ model }) {
  const layoutContext = React.useContext(LayoutContext);
  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the server
  // providing the models instead of the client rendering them.
  return React.createElement(
    model.tagName,
    createElementAttributes(model, layoutContext.sendEvent),
    ...createElementChildren(
      model,
      (model) => html`<${Element} key=${model.key} model=${model} />`
    )
  );
}

function ImportedElement({ model }) {
  const layoutContext = React.useContext(LayoutContext);

  const importSourceFallback = model.importSource.fallback;
  const [importSource, setImportSource] = React.useState(null);

  if (!importSource) {
    // load the import source in the background
    loadModelImportSource(layoutContext, model.importSource).then(
      setImportSource
    );

    // display a fallback if one was given
    if (!importSourceFallback) {
      return html`<div />`;
    } else if (typeof importSourceFallback === "string") {
      return html`<div>${importSourceFallback}</div>`;
    } else {
      return html`<${StandardElement} model=${importSourceFallback} />`;
    }
  } else {
    return html`<${_ImportedElement}
      model=${model}
      importSource=${importSource}
    />`;
  }
}

function _ImportedElement({ model, importSource }) {
  const layoutContext = React.useContext(LayoutContext);
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
