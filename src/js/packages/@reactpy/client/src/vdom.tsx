import React from "react";
import { ReactPyClientInterface } from "./types";
import serializeEvent from "event-to-object";
import {
  ReactPyVdom,
  ReactPyVdomImportSource,
  ReactPyVdomEventHandler,
  ReactPyModule,
  BindImportSource,
  ReactPyModuleBinding,
} from "./types";
import log from "./logger";

export async function loadImportSource(
  vdomImportSource: ReactPyVdomImportSource,
  client: ReactPyClientInterface,
): Promise<BindImportSource> {
  let module: ReactPyModule;
  if (vdomImportSource.sourceType === "URL") {
    module = await import(vdomImportSource.source);
  } else {
    module = await client.loadModule(vdomImportSource.source);
  }
  if (typeof module.bind !== "function") {
    throw new Error(
      `${vdomImportSource.source} did not export a function 'bind'`,
    );
  }

  return (node: HTMLElement) => {
    const binding = module.bind(node, {
      sendMessage: client.sendMessage,
      onMessage: client.onMessage,
    });
    if (
      !(
        typeof binding.create === "function" &&
        typeof binding.render === "function" &&
        typeof binding.unmount === "function"
      )
    ) {
      log.error(`${vdomImportSource.source} returned an impropper binding`);
      return null;
    }

    return {
      render: (model) =>
        binding.render(
          createImportSourceElement({
            client,
            module,
            binding,
            model,
            currentImportSource: vdomImportSource,
          }),
        ),
      unmount: binding.unmount,
    };
  };
}

function createImportSourceElement(props: {
  client: ReactPyClientInterface;
  module: ReactPyModule;
  binding: ReactPyModuleBinding;
  model: ReactPyVdom;
  currentImportSource: ReactPyVdomImportSource;
}): any {
  let type: any;
  if (props.model.importSource) {
    if (
      !isImportSourceEqual(props.currentImportSource, props.model.importSource)
    ) {
      log.error(
        "Parent element import source " +
          stringifyImportSource(props.currentImportSource) +
          " does not match child's import source " +
          stringifyImportSource(props.model.importSource),
      );
      return null;
    } else if (!props.module[props.model.tagName]) {
      log.error(
        "Module from source " +
          stringifyImportSource(props.currentImportSource) +
          ` does not export ${props.model.tagName}`,
      );
      return null;
    } else {
      type = props.module[props.model.tagName];
    }
  } else {
    type = props.model.tagName;
  }
  return props.binding.create(
    type,
    createAttributes(props.model, props.client),
    createChildren(props.model, (child) =>
      createImportSourceElement({
        ...props,
        model: child,
      }),
    ),
  );
}

function isImportSourceEqual(
  source1: ReactPyVdomImportSource,
  source2: ReactPyVdomImportSource,
) {
  return (
    source1.source === source2.source &&
    source1.sourceType === source2.sourceType
  );
}

function stringifyImportSource(importSource: ReactPyVdomImportSource) {
  return JSON.stringify({
    source: importSource.source,
    sourceType: importSource.sourceType,
  });
}

export function createChildren<Child>(
  model: ReactPyVdom,
  createChild: (child: ReactPyVdom) => Child,
): (Child | string)[] {
  if (!model.children) {
    return [];
  } else {
    return model.children.map((child) => {
      switch (typeof child) {
        case "object":
          return createChild(child);
        case "string":
          return child;
      }
    });
  }
}

export function createAttributes(
  model: ReactPyVdom,
  client: ReactPyClientInterface,
): { [key: string]: any } {
  return Object.fromEntries(
    Object.entries({
      // Normal HTML attributes
      ...model.attributes,
      // Construct event handlers
      ...Object.fromEntries(
        Object.entries(model.eventHandlers || {}).map(([name, handler]) =>
          createEventHandler(client, name, handler),
        ),
      ),
      // Convert snake_case to camelCase names
    }).map(normalizeAttribute),
  );
}

function createEventHandler(
  client: ReactPyClientInterface,
  name: string,
  { target, preventDefault, stopPropagation }: ReactPyVdomEventHandler,
): [string, () => void] {
  return [
    name,
    function (...args: any[]) {
      const data = Array.from(args).map((value) => {
        if (!(typeof value === "object" && value.nativeEvent)) {
          return value;
        }
        const event = value as React.SyntheticEvent<any>;
        if (preventDefault) {
          event.preventDefault();
        }
        if (stopPropagation) {
          event.stopPropagation();
        }
        return serializeEvent(event.nativeEvent);
      });
      client.sendMessage({ type: "layout-event", data, target });
    },
  ];
}

function normalizeAttribute([key, value]: [string, any]): [string, any] {
  let normKey = key;
  let normValue = value;

  if (key === "style" && typeof value === "object") {
    normValue = Object.fromEntries(
      Object.entries(value).map(([k, v]) => [snakeToCamel(k), v]),
    );
  } else if (
    key.startsWith("data_") ||
    key.startsWith("aria_") ||
    DASHED_HTML_ATTRS.includes(key)
  ) {
    normKey = key.split("_").join("-");
  } else {
    normKey = snakeToCamel(key);
  }
  return [normKey, normValue];
}

function snakeToCamel(str: string): string {
  return str.replace(/([_][a-z])/g, (group) =>
    group.toUpperCase().replace("_", ""),
  );
}

// see list of HTML attributes with dashes in them:
// https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes#attribute_list
const DASHED_HTML_ATTRS = ["accept_charset", "http_equiv"];
