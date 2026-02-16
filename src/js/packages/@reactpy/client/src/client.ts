import logger from "./logger";
import type {
  ReactPyClientInterface,
  ReactPyModule,
  GenericReactPyClientProps,
  ReactPyUrls,
} from "./types";
import { createReconnectingWebSocket } from "./websocket";

export abstract class BaseReactPyClient implements ReactPyClientInterface {
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

export class ReactPyClient
  extends BaseReactPyClient
  implements ReactPyClientInterface
{
  urls: ReactPyUrls;
  socket: { current?: WebSocket };
  mountElement: HTMLElement;
  private readonly messageQueue: any[] = [];

  constructor(props: GenericReactPyClientProps) {
    super();

    this.urls = props.urls;
    this.mountElement = props.mountElement;
    this.socket = createReconnectingWebSocket({
      url: this.urls.componentUrl,
      readyPromise: this.ready,
      ...props.reconnectOptions,
      onOpen: () => {
        while (this.messageQueue.length > 0) {
          this.sendMessage(this.messageQueue.shift());
        }
      },
      onMessage: async ({ data }) => this.handleIncoming(JSON.parse(data)),
    });
  }

  sendMessage(message: any): void {
    if (
      this.socket.current &&
      this.socket.current.readyState === WebSocket.OPEN
    ) {
      this.socket.current.send(JSON.stringify(message));
    } else {
      this.messageQueue.push(message);
    }
  }

  loadModule(moduleName: string): Promise<ReactPyModule> {
    return import(`${this.urls.jsModulesPath}${moduleName}`);
  }
}
