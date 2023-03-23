import { OutgoingMessage, IncomingMessage } from "./messages";
import { ReactPyModule } from "./reactpy-vdom";
import logger from "./logger";

export interface ReactPyClient {
  start: () => void;
  stop: () => void;
  onMessage: <M extends IncomingMessage>(
    type: M["type"],
    handler: (message: M) => void,
  ) => void;
  sendMessage: (message: OutgoingMessage) => void;
  loadModule: (moduleName: string) => Promise<ReactPyModule>;
}

export type SimpleReactPyClientProprs = {
  serverLocation: UrlProps;
  reconnectOptions?: ReconnectProps;
};

type UrlProps = {
  url: string;
  route: string;
  query: string;
};

type ReconnectProps = {
  maxInterval?: number;
  maxRetries?: number;
  backoffRate?: number;
  intervalJitter?: number;
};

export class SimpleReactPyClient implements ReactPyClient {
  private resolveShouldOpen: (value: unknown) => void;
  private resolveShouldClose: (value: unknown) => void;
  private readonly urls: ServerUrls;
  private readonly handlers: {
    [key in IncomingMessage["type"]]: ((message: any) => void)[];
  };
  private readonly socket: { current?: WebSocket };

  constructor(props: SimpleReactPyClientProprs) {
    this.handlers = {
      "connection-open": [],
      "connection-close": [],
      "layout-update": [],
    };

    this.urls = getServerUrls(props.serverLocation);

    this.resolveShouldOpen = () => {
      throw new Error("Could not start client");
    };
    this.resolveShouldClose = () => {
      throw new Error("Could not stop client");
    };
    const shouldOpen = new Promise((r) => (this.resolveShouldOpen = r));
    const shouldClose = new Promise((r) => (this.resolveShouldClose = r));

    this.socket = startReconnectingWebSocket({
      shouldOpen,
      shouldClose,
      url: this.urls.stream,
      onOpen: () => this.handleIncoming({ type: "connection-open" }),
      onMessage: async ({ data }) => this.handleIncoming(JSON.parse(data)),
      onClose: () => this.handleIncoming({ type: "connection-close" }),
      ...props.reconnectOptions,
    });
  }

  start(): void {
    logger.log("Starting client...");
    this.resolveShouldOpen(undefined);
  }

  stop(): void {
    logger.log("stopping client...");
    this.resolveShouldClose(undefined);
  }

  onMessage<M extends IncomingMessage>(
    type: M["type"],
    handler: (message: M) => void,
  ): void {
    this.handlers[type].push(handler);
  }

  sendMessage(message: OutgoingMessage): void {
    this.socket.current?.send(JSON.stringify(message));
  }

  loadModule(moduleName: string): Promise<ReactPyModule> {
    return import(`${this.urls.modules}/${moduleName}`);
  }

  private handleIncoming(message: IncomingMessage): void {
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

type ServerUrls = {
  base: URL;
  stream: string;
  modules: string;
  assets: string;
};

function getServerUrls(props: UrlProps): ServerUrls {
  const base = new URL(`${props.url || document.location.origin}/_reactpy`);
  const modules = `${base}/modules`;
  const assets = `${base}/assets`;

  const streamProtocol = `ws${base.protocol === "https:" ? "s" : ""}`;
  const streamPath = rtrim(`${base.pathname}/stream${props.route || ""}`, "/");
  const stream = `${streamProtocol}://${base.host}${streamPath}${props.query}`;

  return { base, modules, assets, stream };
}

function startReconnectingWebSocket(
  props: {
    shouldOpen: Promise<any>;
    shouldClose: Promise<any>;
    url: string;
    onOpen: () => void;
    onMessage: (message: MessageEvent<any>) => void;
    onClose: () => void;
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
  let closed = false;
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
      props.onOpen();
    };
    socket.current.onmessage = props.onMessage;
    socket.current.onclose = () => {
      if (!everConnected) {
        logger.log("failed to connect");
        return;
      }

      logger.log("client disconnected");
      props.onClose();

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

  props.shouldOpen.then(connect);
  props.shouldClose.then(() => {
    closed = true;
    socket.current?.close();
  });

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
