import * as react from "react";
import * as reactDOM from "react-dom";
import htm from "htm";
import * as jsonpatch from "fast-json-patch";

import serializeEvent from "./event-to-object";

const html = htm.bind(react.createElement);
const LayoutConfigContext = react.createContext({});

export function mountLayoutWithWebSocket(
  mountElement,
  endpoint,
  importSourceUrl
) {
  if (endpoint.startsWith(".") || endpoint.startsWith("/")) {
    let loc = window.location;
    let protocol;
    if (loc.protocol === "https:") {
      protocol = "wss:";
    } else {
      protocol = "ws:";
    }
    let new_uri = protocol + "//" + loc.host;
    if (endpoint.startsWith(".")) {
      new_url += loc.pathname + "/";
    }
    endpoint = new_uri + endpoint;
  }

  const ws = new WebSocket(endpoint);

  function saveUpdateHook(update) {
    ws.onmessage = (event) => {
      const [pathPrefix, patch] = JSON.parse(event.data);
      update(pathPrefix, patch);
    };
  }

  function sendCallback(event) {
    ws.send(
      JSON.stringify({
        header: {},
        body: { event: event },
      })
    );
  }

  return mountLayout(
    mountElement,
    saveUpdateHook,
    sendCallback,
    importSourceUrl
  );
}

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
  const module = useLazyModule(
    model.importSource.source,
    config.importSourceUrl
  );
  if (module) {
    const cmpt = getPathProperty(module, model.tagName);
    const children = elementChildren(model);
    const attributes = elementAttributes(model, config.sendEvent);
    return html`<${cmpt} ...${attributes}>${children}<//>`;
  } else {
    const fallback = model.importSource.fallback;
    if (!fallback) {
      return html`<div />`;
    }
    switch (typeof fallback) {
      case "object":
        return html`<${Element} model=${fallback} />`;
      case "string":
        return html`<div>${fallback}</div>`;
    }
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

function elementChildren(model) {
  if (!model.children) {
    return [];
  } else {
    return model.children.map((child) => {
      switch (typeof child) {
        case "object":
          return html`<${Element} model=${child} />`;
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

function useLazyModule(source, sourceUrlBase = "") {
  const [module, setModule] = react.useState(null);
  if (!module) {
    // use eval() to avoid weird build behavior by bundlers like Webpack
    eval(`import("${joinUrl(sourceUrlBase, source)}")`).then(setModule);
  }
  return module;
}

function getPathProperty(obj, prop) {
  // properties may be dot seperated strings
  const path = prop.split(".");
  const firstProp = path.shift();
  let value = obj[firstProp];
  for (let i = 0; i < path.length; i++) {
    value = value[path[i]];
  }
  return value;
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

function applyPatchInplace(doc, path, patch) {
  if (!path) {
    jsonpatch.applyPatch(doc, patch);
  } else {
    jsonpatch.applyPatch(doc, [
      {
        op: "replace",
        path: path,
        value: jsonpatch.applyPatch(
          jsonpatch.getValueByPointer(doc, path),
          patch,
          false,
          false
        ).newDocument,
      },
    ]);
  }
}

function useForceUpdate() {
  const [, updateState] = react.useState();
  return react.useCallback(() => updateState({}), []);
}

function joinUrl(base, tail) {
  return tail.startsWith("./")
    ? (base.endsWith("/") ? base.slice(0, -1) : base) + tail.slice(1)
    : tail;
}
