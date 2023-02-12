import { serializeEvent } from "./event-to-object.js";

export function createElementChildren(model, createElement) {
  if (!model.children) {
    return [];
  } else {
    return model.children
      .filter((x) => x) // filter nulls
      .map((child) => {
        switch (typeof child) {
          case "object":
            return createElement(child);
          case "string":
            return child;
        }
      });
  }
}

export function createElementAttributes(model, sendEvent) {
  const attributes = Object.assign({}, model.attributes);

  if (model.eventHandlers) {
    for (const [eventName, eventSpec] of Object.entries(model.eventHandlers)) {
      attributes[eventName] = createEventHandler(sendEvent, eventSpec);
    }
  }

  return Object.fromEntries(Object.entries(attributes).map(normalizeAttribute));
}

function createEventHandler(sendEvent, eventSpec) {
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

function normalizeAttribute([key, value]) {
  let normKey = key;
  let normValue = value;

  if (key === "style" && typeof value === "object") {
    normValue = Object.fromEntries(
      Object.entries(value).map(([k, v]) => [snakeToCamel(k), v])
    );
  } else if (
    key.startsWith("data_") ||
    key.startsWith("aria_") ||
    DASHED_HTML_ATTRS.includes(key)
  ) {
    normKey = key.replaceAll("_", "-");
  } else {
    normKey = snakeToCamel(key);
  }
  return [normKey, normValue];
}

function snakeToCamel(str) {
  return str.replace(/([_][a-z])/g, (group) =>
    group.toUpperCase().replace("_", "")
  );
}

// see list of HTML attributes with dashes in them:
// https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes#attribute_list
const DASHED_HTML_ATTRS = ["accept_charset", "http_equiv"];
