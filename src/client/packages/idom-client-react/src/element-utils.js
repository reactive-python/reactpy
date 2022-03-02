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
      attributes[eventName] = createEventHandler(
        eventName,
        sendEvent,
        eventSpec
      );
    }
  }

  return attributes;
}

function createEventHandler(eventName, sendEvent, eventSpec) {
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
