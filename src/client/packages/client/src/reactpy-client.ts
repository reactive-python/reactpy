import { OutgoingMessage, IncomingMessage } from "./messages";
import { ReactPyModule } from "./reactpy-vdom";

export interface ReactPyClient {
  receiveMessage: <M extends IncomingMessage>(type: M["type"]) => Promise<M>;
  sendMessage: (message: OutgoingMessage) => Promise<void>;
  loadModule: (moduleName: string) => Promise<ReactPyModule>;
}

type UrlProps = {
  baseUrl: string;
  routePath: string;
  queryString: string;
};

type ReconnectProps = {
  maxInterval?: number;
  maxRetries?: number;
  backoffRate?: number;
  intervalJitter?: number;
};

export class SimpleReactPyClient implements ReactPyClient {
  private readonly urls: ServerUrls;
  private readonly handlers: {
    [key in IncomingMessage["type"]]?: ((message: any) => void)[];
  };
  private readonly socket: { current?: WebSocket };

  constructor(props: {
    serverApi: UrlProps;
    reconnectOptions?: ReconnectProps;
  }) {
    this.handlers = {};

    this.urls = getServerUrls(props.serverApi);

    this.socket = startReconnectingWebSocket({
      url: this.urls.stream,
      onOpen: () => this.handleIncoming({ type: "connection-open" }),
      onMessage: ({ data }) => this.handleIncoming(JSON.parse(data)),
      onClose: () => this.handleIncoming({ type: "connection-close" }),

      ...props.reconnectOptions,
    });
  }

  async receiveMessage<M extends IncomingMessage>(type: M["type"]): Promise<M> {
    let handlers: ((message: any) => void)[];
    if (type in this.handlers) {
      handlers = this.handlers[type] as any;
    } else {
      handlers = [];
      this.handlers[type] = handlers;
    }
    return new Promise((r) => handlers.push(r));
  }

  async sendMessage(message: OutgoingMessage): Promise<void> {
    this.socket.current?.send(JSON.stringify(message));
  }

  loadModule(moduleName: string): Promise<ReactPyModule> {
    return import(`${this.urls.modules}/${moduleName}`);
  }

  private handleIncoming(message: IncomingMessage): void {
    if (!message.type) {
      console.warn("Received message without type", message);
      return;
    }

    const messageHandlers: ((m: any) => void)[] | undefined =
      this.handlers[message.type];
    if (!messageHandlers) {
      console.warn("Received message without handler", message);
      return;
    }

    messageHandlers.forEach((h) => h(message));
    delete this.handlers[message.type];
  }
}

type ServerUrls = {
  base: URL;
  stream: string;
  modules: string;
  assets: string;
};

function getServerUrls(props: UrlProps): ServerUrls {
  const base = new URL(`${props.baseUrl || document.location.origin}/_reactpy`);
  const modules = `${base}/modules`;
  const assets = `${base}/assets`;

  const streamProtocol = `ws${base.protocol === "https:" ? "s" : ""}`;
  const streamPath = `${base.pathname}/stream${props.routePath || ""}`;
  const stream = `${streamProtocol}://${base.host}${streamPath}`;

  return { base, modules, assets, stream };
}

function startReconnectingWebSocket(
  props: {
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

  let retries = 0;
  let interval = 200;
  const socket: { current?: WebSocket } = {};

  const connect = () => {
    socket.current = new WebSocket(props.url);
    socket.current.onopen = () => {
      interval = 0;
      retries = 0;
      props.onOpen();
    };
    socket.current.onmessage = props.onMessage;
    socket.current.onclose = () => {
      props.onClose();
      if (retries >= maxRetries) {
        return;
      }
      setTimeout(connect, interval);
      interval = nextInterval(
        interval,
        backoffRate,
        maxInterval,
        intervalJitter,
      );
      retries++;
    };
  };

  connect();

  return socket;
}

function nextInterval(
  currentInterval: number,
  backoffRate: number,
  maxInterval: number,
  intervalJitter: number,
) {
  return Math.min(
    currentInterval *
      // increase interval by backoff rate
      backoffRate +
      // add random jitter
      (Math.random() * intervalJitter * 2 - intervalJitter),
    // don't exceed max interval
    maxInterval,
  );
}
