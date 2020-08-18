import React, {
  useEffect,
  useState,
  useMemo,
  Suspense,
} from "../web_modules/react.js";

import ReactDOM from "../web_modules/react-dom.js";
import htm from "../web_modules/htm.js";
import * as jsonpatch from "../web_modules/fast-json-patch.js";

import serializeEvent from "./event-to-object.js";

const html = htm.bind(React.createElement);
const alreadyImported = {};

export function renderLayout(mountElement, endpoint) {
  const cmpt = html`<${Layout} endpoint=${endpoint} />`;
  return ReactDOM.render(cmpt, mountElement);
}

export default function Layout({ endpoint }) {
  // handle relative endpoint URI
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

  const socket = useMemo(() => new WebSocket(endpoint), [endpoint]);
  const [state, setState] = useState({ model: {} });

  socket.onmessage = (event) => {
    const [pathPrefix, patch] = JSON.parse(event.data);
    setState({
      model: jsonpatch.applyPatch(
        state.model,
        patch.map((op) => {
          op.path = pathPrefix + op.path;
          return op;
        }),
        undefined,
        false
      ).newDocument,
    });
  };

  const sendMsg = (msg) => {
    socket.send(JSON.stringify(msg));
  };
  const sendEvent = (event) => {
    sendMsg({
      header: {},
      body: { event: event },
    });
  };

  if (state.model.tagName) {
    return html`<${Element} sendEvent=${sendEvent} model=${state.model} />`;
  } else {
    return html`<div />`;
  }
}

function Element({ sendEvent, model }) {
  if (model.importSource) {
    return html`<${LazyElement} sendEvent=${sendEvent} model=${model} />`;
  } else {
    const children = elementChildren(sendEvent, model);
    const attributes = elementAttributes(sendEvent, model);
    if (model.children && model.children.length) {
      return html`<${model.tagName} ...${attributes}>${children}<//>`;
    } else {
      return html`<${model.tagName} ...${attributes} />`;
    }
  }
}

function LazyElement({ sendEvent, model }) {
  const module = useLazyModule(model.importSource.source);
  if (module) {
    const cmpt = getPathProperty(module, model.tagName);
    const children = elementChildren(sendEvent, model);
    const attributes = elementAttributes(sendEvent, model);
    return html`<${cmpt} ...${attributes}>${children}<//>`;
  } else {
    return html`<div>${model.importSource.fallback}<//>`;
  }
}

function elementChildren(sendEvent, model) {
  if (!model.children) {
    return [];
  } else {
    return model.children.map((child) => {
      switch (typeof child) {
        case "object":
          return html` <${Element} model=${child} sendEvent=${sendEvent} /> `;
        case "string":
          return child;
      }
    });
  }
}

function elementAttributes(sendEvent, model) {
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

function useLazyModule(source) {
  const [module, setModule] = useState(alreadyImported[source]);
  if (!module) {
    dynamicImport(source).then(setModule);
  }
  return module;
}

function dynamicImport(source) {
  return eval(`import('${source}')`).then(
    (pkg) => (pkg.default ? pkg.default : pkg),
    (error) => {
      if (!error.stack) {
        throw error;
      } else {
        console.log(error);
        return {
          default: function Catch() {
            return html`
              <pre>
                  <h1>Error</h1>
                  <code>${[error.stack, error.message]}</code>
                </pre
              >
            `;
          },
        };
      }
    }
  );
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
