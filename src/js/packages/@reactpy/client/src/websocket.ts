import type { CreateReconnectingWebSocketProps } from "./types";
import log from "./logger";

function syncBrowserLocation(url: URL): void {
  // The window will always have a HTTP path, so ReactPy should always be aware of it.
  url.searchParams.set("path", window.location.pathname);

  if (window.location.search) {
    // Set the query string parameter if the HTTP location has a query string.
    url.searchParams.set("qs", window.location.search);
  } else {
    // Remove any existing (potentially stale) query string parameter if the current location doesn't have one
    url.searchParams.delete("qs");
  }
}

export function createReconnectingWebSocket(
  props: CreateReconnectingWebSocketProps,
) {
  const { interval, maxInterval, maxRetries, backoffMultiplier } = props;
  let retries = 0;
  let currentInterval = interval;
  let everConnected = false;
  const closed = false;
  const socket: { current?: WebSocket } = {};

  const connect = () => {
    if (closed) {
      return;
    }
    syncBrowserLocation(props.url);
    socket.current = new WebSocket(props.url);
    socket.current.onopen = () => {
      everConnected = true;
      log.info("Connected!");
      currentInterval = interval;
      retries = 0;
      if (props.onOpen) {
        props.onOpen();
      }
    };
    socket.current.onmessage = (event) => {
      if (props.onMessage) {
        props.onMessage(event);
      }
    };
    socket.current.onclose = () => {
      if (props.onClose) {
        props.onClose();
      }
      if (!everConnected) {
        log.info("Failed to connect!");
        return;
      }
      log.info("Disconnected!");
      if (retries >= maxRetries) {
        log.info("Connection max retries exhausted!");
        return;
      }
      log.info(
        `Reconnecting in ${(currentInterval / 1000).toPrecision(4)} seconds...`,
      );
      setTimeout(connect, currentInterval);
      currentInterval = nextInterval(
        currentInterval,
        backoffMultiplier,
        maxInterval,
      );
      retries++;
    };
  };

  props.readyPromise.then(() => log.info("Starting client...")).then(connect);

  return socket;
}

export function nextInterval(
  currentInterval: number,
  backoffMultiplier: number,
  maxInterval: number,
): number {
  return Math.min(
    // increase interval by backoff multiplier
    currentInterval * backoffMultiplier,
    // don't exceed max interval
    maxInterval,
  );
}
