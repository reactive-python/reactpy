import { CreateReconnectingWebSocketProps } from "./types";
import log from "./logger";

export function createReconnectingWebSocket(
  props: CreateReconnectingWebSocketProps,
) {
  const { startInterval, maxInterval, maxRetries, backoffMultiplier } = props;
  let retries = 0;
  let interval = startInterval;
  let everConnected = false;
  const closed = false;
  const socket: { current?: WebSocket } = {};

  const connect = () => {
    if (closed) {
      return;
    }
    socket.current = new WebSocket(props.url);
    socket.current.onopen = () => {
      everConnected = true;
      log.info("ReactPy connected!");
      interval = startInterval;
      retries = 0;
      if (props.onOpen) {
        props.onOpen();
      }
    };
    socket.current.onmessage = props.onMessage;
    socket.current.onclose = () => {
      if (props.onClose) {
        props.onClose();
      }
      if (!everConnected) {
        log.info("ReactPy failed to connect!");
        return;
      }
      log.info("ReactPy disconnected!");
      if (retries >= maxRetries) {
        log.info("ReactPy connection max retries exhausted!");
        return;
      }
      log.info(
        `ReactPy reconnecting in ${(interval / 1000).toPrecision(4)} seconds...`,
      );
      setTimeout(connect, interval);
      interval = nextInterval(interval, backoffMultiplier, maxInterval);
      retries++;
    };
  };

  props.readyPromise
    .then(() => log.info("Starting ReactPy client..."))
    .then(connect);

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
