import type { ReactPyClientInterface } from "./types";
import eventToObject from "event-to-object";
import type {
  ReactPyVdom,
  ReactPyVdomImportSource,
  ReactPyVdomEventHandler,
  ReactPyModule,
  BindImportSource,
  ReactPyModuleBinding,
  ImportSourceBinding,
} from "./types";
import { infer_bind_from_environment } from "./bind";
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

  let { bind } = module;
  if (typeof bind !== "function") {
    bind = await infer_bind_from_environment();
  }

  return (node: HTMLElement) => {
    const binding = bind(node, {
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
      return props.binding.create("reactpy-child", {
        ref: (node: ReactPyChild | null) => {
          if (node) {
            node.client = props.client;
            node.model = props.model;
            node.requestUpdate();
          }
        },
      });
    } else {
      type = getComponentFromModule(
        props.module,
        props.model.tagName,
        props.model.importSource,
      );
      if (!type) {
        // Error message logged within getComponentFromModule
        return null;
      }
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

function getComponentFromModule(
  module: ReactPyModule,
  componentName: string,
  importSource: ReactPyVdomImportSource,
): any {
  /*  Gets the component with the provided name from the provided module.

  Built specifically to work on inifinitely deep nested components.
  For example, component "My.Nested.Component" is accessed from
  ModuleA like so: ModuleA["My"]["Nested"]["Component"].
  */
  const componentParts: string[] = componentName.split(".");
  let Component: any = null;
  for (let i = 0; i < componentParts.length; i++) {
    const iterAttr = componentParts[i];
    Component = i == 0 ? module[iterAttr] : Component[iterAttr];
    if (!Component) {
      if (i == 0) {
        log.error(
          "Module from source " +
            stringifyImportSource(importSource) +
            ` does not export ${iterAttr}`,
        );
      } else {
        console.error(
          `Component ${componentParts.slice(0, i).join(".")} from source ` +
            stringifyImportSource(importSource) +
            ` does not have subcomponent ${iterAttr}`,
        );
      }
      break;
    }
  }
  return Component;
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
      ...Object.fromEntries(
        Object.entries(model.inlineJavaScript || {}).map(
          ([name, inlineJavaScript]) =>
            createInlineJavaScript(name, inlineJavaScript),
        ),
      ),
    }),
  );
}

function createEventHandler(
  client: ReactPyClientInterface,
  name: string,
  { target, preventDefault, stopPropagation }: ReactPyVdomEventHandler,
): [string, () => void] {
  const eventHandler = function (...args: any[]) {
    const data = Array.from(args).map((value) => {
      const event = value as Event;
      if (preventDefault) {
        event.preventDefault();
      }
      if (stopPropagation) {
        event.stopPropagation();
      }

      // Convert JavaScript objects to plain JSON, if needed
      if (typeof event === "object") {
        return eventToObject(event);
      } else {
        return event;
      }
    });
    client.sendMessage({ type: "layout-event", data, target });
  };
  eventHandler.isHandler = true;
  return [name, eventHandler];
}

function createInlineJavaScript(
  name: string,
  inlineJavaScript: string,
): [string, () => void] {
  /* Function that will execute the string-like InlineJavaScript
  via eval in the most appropriate way */
  const wrappedExecutable = function (...args: any[]) {
    function handleExecution(...args: any[]) {
      const evalResult = eval(inlineJavaScript);
      if (typeof evalResult == "function") {
        return evalResult(...args);
      }
    }
    if (args.length > 0 && args[0] instanceof Event) {
      /* If being triggered by an event, set the event's current
      target to "this". This ensures that inline
      javascript statements such as the following work:
      html.button({"onclick": 'this.value = "Clicked!"'}, "Click Me")*/
      return handleExecution.call(args[0].currentTarget, ...args);
    } else {
      /* If not being triggered by an event, do not set "this" and
      just call normally */
      return handleExecution(...args);
    }
  };
  wrappedExecutable.isHandler = false;
  return [name, wrappedExecutable];
}

class ReactPyChild extends HTMLElement {
  mountPoint: HTMLDivElement;
  binding: ImportSourceBinding | null = null;
  _client: ReactPyClientInterface | null = null;
  _model: ReactPyVdom | null = null;
  currentImportSource: ReactPyVdomImportSource | null = null;

  constructor() {
    super();
    this.mountPoint = document.createElement("div");
    this.mountPoint.style.display = "contents";
  }

  connectedCallback() {
    this.appendChild(this.mountPoint);
  }

  set client(value: ReactPyClientInterface) {
    this._client = value;
  }

  set model(value: ReactPyVdom) {
    this._model = value;
  }

  requestUpdate() {
    this.update();
  }

  async update() {
    if (!this._client || !this._model || !this._model.importSource) {
      return;
    }

    const newImportSource = this._model.importSource;

    if (
      !this.binding ||
      !this.currentImportSource ||
      !isImportSourceEqual(this.currentImportSource, newImportSource)
    ) {
      if (this.binding) {
        this.binding.unmount();
        this.binding = null;
      }

      this.currentImportSource = newImportSource;

      try {
        const bind = await loadImportSource(newImportSource, this._client);
        if (
          this.isConnected &&
          this.currentImportSource &&
          isImportSourceEqual(this.currentImportSource, newImportSource)
        ) {
          const oldBinding = this.binding as ImportSourceBinding | null;
          if (oldBinding) {
            oldBinding.unmount();
          }
          this.binding = bind(this.mountPoint);
          if (this.binding) {
            this.binding.render(this._model);
          }
        }
      } catch (error) {
        console.error("Failed to load import source", error);
      }
    } else {
      if (this.binding) {
        this.binding.render(this._model);
      }
    }
  }

  disconnectedCallback() {
    if (this.binding) {
      this.binding.unmount();
      this.binding = null;
      this.currentImportSource = null;
    }
  }
}

if (
  typeof customElements !== "undefined" &&
  !customElements.get("reactpy-child")
) {
  customElements.define("reactpy-child", ReactPyChild);
}
