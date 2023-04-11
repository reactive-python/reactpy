import { ReactPyModule } from "./reactpy-vdom";
import logger from "./logger";

/**
 * A client for communicating with a ReactPy server.
 */
export interface ReactPyClient {
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

export abstract class BaseReactPyClient implements ReactPyClient {
  private readonly handlers: { [key: string]: ((message: any) => void)[] } = {};
  protected readonly ready: Promise<void>;
  private resolveReady: (value: undefined) => void;

  constructor() {
    this.resolveReady = () => {};
    this.ready = new Promise((resolve) => (this.resolveReady = resolve));
  }

  onMessage(type: string, handler: (message: any) => void): () => void {
    (this.handlers[type] || (this.handlers[type] = [])).push(handler);
    this.resolveReady(undefined);
    return () => {
      this.handlers[type] = this.handlers[type].filter((h) => h !== handler);
    };
  }

  abstract sendMessage(message: any): void;
  abstract loadModule(moduleName: string): Promise<ReactPyModule>;

  /**
   * Handle an incoming message.
   *
   * This should be called by subclasses when a message is received.
   *
   * @param message The message to handle. The message must have a `type` property.
   */
  protected handleIncoming(message: any): void {
    if (!message.type) {
      logger.warn("Received message without type", message);
      return;
    }

    const messageHandlers: ((m: any) => void)[] | undefined =
      this.handlers[message.type];
    if (!messageHandlers) {
      logger.warn("Received message without handler", message);
      return;
    }

    messageHandlers.forEach((h) => h(message));
  }
}

export type SimpleReactPyClientProps = {
  serverLocation?: LocationProps;
  reconnectOptions?: ReconnectProps;
};

/**
 * The location of the server.
 *
 * This is used to determine the location of the server's API endpoints. All endpoints
 * are expected to be found at the base URL, with the following paths:
 *
 * - `_reactpy/stream/${route}${query}`: The websocket endpoint for the stream.
 * - `_reactpy/modules`: The directory containing the dynamically loaded modules.
 * - `_reactpy/assets`: The directory containing the static assets.
 */
type LocationProps = {
  /**
   * The base URL of the server.
   *
   * @default - document.location.origin
   */
  url: string;
  /**
   * The route to the page being rendered.
   *
   * @default - document.location.pathname
   */
  route: string;
  /**
   * The query string of the page being rendered.
   *
   * @default - document.location.search
   */
  query: string;
};

type ReconnectProps = {
  maxInterval?: number;
  maxRetries?: number;
  backoffRate?: number;
  intervalJitter?: number;
};

export class SimpleReactPyClient
  extends BaseReactPyClient
  implements ReactPyClient
{
  private readonly urls: ServerUrls;
  private readonly socket: { current?: WebSocket };

  constructor(props: SimpleReactPyClientProps) {
    super();

    this.urls = getServerUrls(
      props.serverLocation || {
        url: document.location.origin,
        route: document.location.pathname,
        query: document.location.search,
      },
    );

    this.socket = createReconnectingWebSocket({
      readyPromise: this.ready,
      url: this.urls.stream,
      onMessage: async ({ data }) => this.handleIncoming(JSON.parse(data)),
      ...props.reconnectOptions,
    });
  }

  sendMessage(message: any): void {
    this.socket.current?.send(JSON.stringify(message));
  }

  loadModule(moduleName: string): Promise<ReactPyModule> {
    return import(`${this.urls.modules}/${moduleName}`);
  }
}

type ServerUrls = {
  base: URL;
  stream: string;
  modules: string;
  assets: string;
};

function getServerUrls(props: LocationProps): ServerUrls {
  const base = new URL(`${props.url || document.location.origin}/_reactpy`);
  const modules = `${base}/modules`;
  const assets = `${base}/assets`;

  const streamProtocol = `ws${base.protocol === "https:" ? "s" : ""}`;
  const streamPath = rtrim(`${base.pathname}/stream${props.route || ""}`, "/");
  const stream = `${streamProtocol}://${base.host}${streamPath}${props.query}`;

  return { base, modules, assets, stream };
}

function createReconnectingWebSocket(
  props: {
    url: string;
    readyPromise: Promise<void>;
    onOpen?: () => void;
    onMessage: (message: MessageEvent<any>) => void;
    onClose?: () => void;
  } & ReconnectProps,
) {
  const {
    maxInterval = 60000,
    maxRetries = 50,
    backoffRate = 1.1,
    intervalJitter = 0.1,
  } = props;

  const startInterval = 750;
  let retries = 0;
  let interval = startInterval;
  const closed = false;
  let everConnected = false;
  const socket: { current?: WebSocket } = {};

  const connect = () => {
    if (closed) {
      return;
    }
    socket.current = new WebSocket(props.url);
    socket.current.onopen = () => {
      everConnected = true;
      logger.log("client connected");
      interval = startInterval;
      retries = 0;
      if (props.onOpen) {
        props.onOpen();
      }
    };
    socket.current.onmessage = props.onMessage;
    socket.current.onclose = () => {
      if (!everConnected) {
        logger.log("failed to connect");
        return;
      }

      logger.log("client disconnected");
      if (props.onClose) {
        props.onClose();
      }

      if (retries >= maxRetries) {
        return;
      }

      const thisInterval = addJitter(interval, intervalJitter);
      logger.log(
        `reconnecting in ${(thisInterval / 1000).toPrecision(4)} seconds...`,
      );
      setTimeout(connect, thisInterval);
      interval = nextInterval(interval, backoffRate, maxInterval);
      retries++;
    };
  };

  props.readyPromise.then(() => logger.log("starting client...")).then(connect);

  return socket;
}

function nextInterval(
  currentInterval: number,
  backoffRate: number,
  maxInterval: number,
): number {
  return Math.min(
    currentInterval *
      // increase interval by backoff rate
      backoffRate,
    // don't exceed max interval
    maxInterval,
  );
}

function addJitter(interval: number, jitter: number): number {
  return interval + (Math.random() * jitter * interval * 2 - jitter * interval);
}

function rtrim(text: string, trim: string): string {
  return text.replace(new RegExp(`${trim}+$`), "");
}
