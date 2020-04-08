import { h } from "../web_modules/preact.js";
import {
  useReducer,
  useEffect,
  useState,
  useMemo,
} from "../web_modules/preact/hooks.js";
import htm from "../web_modules/htm.js";
import { Suspense } from "../web_modules/preact/compat.js";

import serializeEvent from "./event-to-object.js";
import lazyComponent from "./lazy-component.js";

const html = htm.bind(h);

function Layout({ endpoint }) {
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

  const socket = useMemo(() => {
    return new WebSocket(endpoint);
  }, [endpoint]);

  const [modelState, setModelState] = useState({ root: null, models: {} });

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const newModels = { ...modelState.models, ...msg.body.render.new };
    msg.body.render.old.forEach((elementId) => delete newModels[elementId]);
    setModelState({ root: msg.body.render.root, models: newModels });
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

  if (modelState.root) {
    return html`<${Element}
      modelState=${modelState}
      model=${modelState.models[modelState.root]}
      sendEvent=${sendEvent}
    />`;
  } else {
    return html`<div />`;
  }
}

function Element({ modelState, model, sendEvent }) {
  const children = elementChildren(modelState, model, sendEvent);
  const attributes = elementAttributes(model, sendEvent);
  if (model.importSource) {
    const lazy = lazyComponent(model);
    return html`
      <Suspense fallback="${model.importSource.fallback}">
        ${h(lazy, attributes, children)}
      </Suspense>
    `;
  } else if (model.children && model.children.length) {
    return html`<${model.tagName} ...${attributes}>${children}<//>`;
  } else {
    return html`<${model.tagName} ...${attributes} />`;
  }
}

function elementChildren(modelState, model, sendEvent) {
  if (!model.children) {
    return [];
  } else {
    return model.children.map((child) => {
      switch (child.type) {
        case "ref":
          return html`
            <${Element}
              modelState=${modelState}
              model=${modelState.models[child.data]}
              sendEvent=${sendEvent}
            />
          `;
        case "obj":
          return html`
            <${Element}
              modelState=${modelState}
              model=${child.data}
              sendEvent=${sendEvent}
            />
          `;
        case "str":
          return child.data;
      }
    });
  }
}

function elementAttributes(model, sendEvent) {
  const attributes = Object.assign({}, model.attributes);

  if (model.eventHandlers) {
    Object.keys(model.eventHandlers).forEach((eventName) => {
      const eventSpec = model.eventHandlers[eventName];
      attributes[eventName] = function (event) {
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
    });
  }

  return attributes;
}

export default Layout;
