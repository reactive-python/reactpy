import React from "react";
import ReactDOM from "react-dom";
import htm from "htm";

import { useJsonPatchCallback } from "./json-patch.js";
import { useImportSource } from "./import-source.js";
import { LayoutContext } from "./contexts.js";

import {
  createElementAttributes,
  createElementChildren,
} from "./element-utils.js";

const html = htm.bind(React.createElement);

export function Layout({ saveUpdateHook, sendEvent, loadImportSource }) {
  const [model, patchModel] = useJsonPatchCallback({});

  React.useEffect(() => saveUpdateHook(patchModel), [patchModel]);

  if (!Object.keys(model).length) {
    return html`<${React.Fragment} />`;
  }

  return html`
    <${LayoutContext.Provider} value=${{ sendEvent, loadImportSource }}>
      <${Element} model=${model} />
    <//>
  `;
}

export function Element({ model }) {
  if (model.error !== undefined) {
    if (model.error) {
      return html`<pre>${model.error}</pre>`;
    } else {
      return null;
    }
  } else if (model.tagName == "script") {
    return html`<${ScriptElement} model=${model} />`;
  } else if (["input", "select", "textarea"].includes(model.tagName)) {
    return html`<${UserInputElement} model=${model} />`;
  } else if (model.importSource) {
    return html`<${ImportedElement} model=${model} />`;
  } else {
    return html`<${StandardElement} model=${model} />`;
  }
}

function StandardElement({ model }) {
  const layoutContext = React.useContext(LayoutContext);

  let type;
  if (model.tagName == "") {
    type = React.Fragment;
  } else {
    type = model.tagName;
  }

  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the server
  // providing the models instead of the client rendering them.
  return React.createElement(
    type,
    createElementAttributes(model, layoutContext.sendEvent),
    ...createElementChildren(
      model,
      (model) => html`<${Element} key=${model.key} model=${model} />`
    )
  );
}

// Element with a value attribute controlled by user input
function UserInputElement({ model }) {
  const ref = React.useRef();
  const layoutContext = React.useContext(LayoutContext);

  const props = createElementAttributes(model, layoutContext.sendEvent);

  // Because we handle events asynchronously, we must leave the value uncontrolled in
  // order to allow all changes committed by the user to be recorded in the order they
  // occur. If we don't the user may commit multiple changes before we render next
  // causing the content of prior changes to be overwritten by subsequent changes.
  let value = props.value;
  delete props.value;

  // Track a buffer of observed values in order to avoid flicker
  const observedValues = React.useState([])[0];

  // Instead of controlling the value, we set it in an effect.
  React.useEffect(() => {
    if (observedValues) {
      if (value === observedValues[0]) {
        observedValues.shift();
        // no need to set a new value yet
        value = undefined;
      } else {
        observedValues.length = 0;
      }
    }
    if (value !== undefined) {
      ref.current.value = value;
    }
  }, [ref.current, value]);

  const givenOnInput = props.onInput;
  props.onInput = (event) => {
    observedValues.push(event.target.value);
    if (typeof givenOnInput === "function") {
      givenOnInput(event);
    }
  };

  // Use createElement here to avoid warning about variable numbers of children not
  // having keys. Warning about this must now be the responsibility of the server
  // providing the models instead of the client rendering them.
  return React.createElement(
    model.tagName,
    {
      ...props,
      ref: (target) => {
        ref.current = target;
      },
    },
    ...createElementChildren(
      model,
      (model) => html`<${Element} key=${model.key} model=${model} />`
    )
  );
}

function ScriptElement({ model }) {
  const ref = React.useRef();
  React.useEffect(() => {
    if (model?.children?.length > 1) {
      console.error("Too many children for 'script' element.");
    }

    let scriptContent = model?.children?.[0];

    let scriptElement;
    if (model.attributes) {
      scriptElement = document.createElement("script");
      for (const [k, v] of Object.entries(model.attributes)) {
        scriptElement.setAttribute(k, v);
      }
      scriptElement.appendChild(document.createTextNode(scriptContent));
      ref.current.appendChild(scriptElement);
    } else {
      let scriptResult = eval(scriptContent);
      if (typeof scriptResult == "function") {
        return scriptResult();
      }
    }
  }, [model.key]);
  return html`<div ref=${ref} />`;
}

function ImportedElement({ model }) {
  const layoutContext = React.useContext(LayoutContext);

  const importSourceFallback = model.importSource.fallback;
  const importSource = useImportSource(model.importSource);

  if (!importSource) {
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
