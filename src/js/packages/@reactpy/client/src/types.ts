import { ComponentType } from "react";

// #### CONNECTION TYPES ####

export type ReconnectOptions = {
  interval: number;
  maxInterval: number;
  maxRetries: number;
  backoffMultiplier: number;
};

export type CreateReconnectingWebSocketProps = {
  url: URL;
  readyPromise: Promise<void>;
  onMessage: (message: MessageEvent<any>) => void;
  onOpen?: () => void;
  onClose?: () => void;
  interval: number;
  maxInterval: number;
  maxRetries: number;
  backoffMultiplier: number;
};

export type ReactPyUrls = {
  componentUrl: URL;
  jsModulesPath: string;
};

export type GenericReactPyClientProps = {
  urls: ReactPyUrls;
  reconnectOptions: ReconnectOptions;
  mountElement: HTMLElement;
};

export type MountProps = {
  mountElement: HTMLElement;
  pathPrefix: string;
  componentPath?: string;
  reconnectInterval?: number;
  reconnectMaxInterval?: number;
  reconnectMaxRetries?: number;
  reconnectBackoffMultiplier?: number;
};

// #### COMPONENT TYPES ####

export type ReactPyComponent = ComponentType<{ model: ReactPyVdom }>;

export type ReactPyVdom = {
  tagName: string;
  key?: string;
  attributes?: { [key: string]: string };
  children?: (ReactPyVdom | string)[];
  error?: string;
  eventHandlers?: { [key: string]: ReactPyVdomEventHandler };
  inlineJavaScript?: { [key: string]: string };
  importSource?: ReactPyVdomImportSource;
};

export type ReactPyVdomEventHandler = {
  target: string;
  preventDefault?: boolean;
  stopPropagation?: boolean;
};

export type ReactPyVdomImportSource = {
  source: string;
  sourceType?: "URL" | "NAME";
  fallback?: string | ReactPyVdom;
  unmountBeforeUpdate?: boolean;
};

export type ReactPyModule = {
  bind: (
    node: HTMLElement,
    context: ReactPyModuleBindingContext,
  ) => ReactPyModuleBinding;
} & { [key: string]: any };

export type ReactPyModuleBindingContext = {
  sendMessage: ReactPyClientInterface["sendMessage"];
  onMessage: ReactPyClientInterface["onMessage"];
};

export type ReactPyModuleBinding = {
  create: (
    type: any,
    props?: any,
    children?: (any | string | ReactPyVdom)[],
  ) => any;
  render: (element: any) => void;
  unmount: () => void;
};

export type BindImportSource = (
  node: HTMLElement,
) => ImportSourceBinding | null;

export type ImportSourceBinding = {
  render: (model: ReactPyVdom) => void;
  unmount: () => void;
};

// #### MESSAGE TYPES ####

export type LayoutUpdateMessage = {
  type: "layout-update";
  path: string;
  model: ReactPyVdom;
};

export type LayoutEventMessage = {
  type: "layout-event";
  target: string;
  data: any;
};

export type IncomingMessage = LayoutUpdateMessage;
export type OutgoingMessage = LayoutEventMessage;
export type Message = IncomingMessage | OutgoingMessage;

// #### INTERFACES ####

/**
 * A client for communicating with a ReactPy server.
 */
export interface ReactPyClientInterface {
  /**
   * Register a handler for a message type.
   *
   * The first time this is called, the client will be considered ready.
   *
   * @param type The type of message to handle.
   * @param handler The handler to call when a message of the given type is received.
   * @returns A function to unregister the handler.
   */
  onMessage(type: string, handler: (message: any) => void): () => void;

  /**
   * Send a message to the server.
   *
   * @param message The message to send. Messages must have a `type` property.
   */
  sendMessage(message: any): void;

  /**
   * Load a module from the server.
   * @param moduleName The name of the module to load.
   * @returns A promise that resolves to the module.
   */
  loadModule(moduleName: string): Promise<ReactPyModule>;
}
