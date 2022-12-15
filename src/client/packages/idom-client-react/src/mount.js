import React from "react";
import ReactDOM from "react-dom";
import { Layout } from "./components.js";

export function mountLayout(mountElement, layoutProps) {
  ReactDOM.render(React.createElement(Layout, layoutProps), mountElement);
}

export function mountLayoutWithWebSocket(
  element,
  endpoint,
  loadImportSource,
  maxReconnectTimeout
) {
  mountLayoutWithReconnectingWebSocket(
    element,
    endpoint,
    loadImportSource,
    maxReconnectTimeout
  );
}

function mountLayoutWithReconnectingWebSocket(
  element,
  endpoint,
  loadImportSource,
  maxReconnectTimeout,
  mountState = {
    everMounted: false,
    reconnectAttempts: 0,
    reconnectTimeoutRange: 0,
  }
) {
  const socket = new WebSocket(endpoint);

  const updateHookPromise = new LazyPromise();

  socket.onopen = (event) => {
    console.info(`IDOM WebSocket connected.`);

    socket.send(JSON.stringify({ type: "client-info", version: "0.0.1" }));

    if (mountState.everMounted) {
      ReactDOM.unmountComponentAtNode(element);
    }
    _resetOpenMountState(mountState);

    mountLayout(element, {
      loadImportSource,
      saveUpdateHook: updateHookPromise.resolve,
      sendEvent: (event) =>
        socket.send(JSON.stringify({ type: "layout-event", data: event })),
    });
  };

  const messageHandlers = {
    "server-info": () => {},
    "layout-update": ({ data }) =>
      updateHookPromise.promise.then((update) => update(data)),
  };

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const handler = messageHandlers[msg["type"]];
    if (!handler) {
      console.error(`Unknown message type '${msg["type"]}'`);
      return;
    }
    handler(msg);
  };

  socket.onclose = (event) => {
    if (!maxReconnectTimeout) {
      console.info(`IDOM WebSocket connection lost.`);
      return;
    }

    const reconnectTimeout = _nextReconnectTimeout(
      maxReconnectTimeout,
      mountState
    );

    console.info(
      `IDOM WebSocket connection lost. Reconnecting in ${reconnectTimeout} seconds...`
    );

    setTimeout(function () {
      mountState.reconnectAttempts++;
      mountLayoutWithReconnectingWebSocket(
        element,
        endpoint,
        loadImportSource,
        maxReconnectTimeout,
        mountState
      );
    }, reconnectTimeout * 1000);
  };
}

function _resetOpenMountState(mountState) {
  mountState.everMounted = true;
  mountState.reconnectAttempts = 0;
  mountState.reconnectTimeoutRange = 0;
}

function _nextReconnectTimeout(maxReconnectTimeout, mountState) {
  const timeout =
    Math.floor(Math.random() * mountState.reconnectTimeoutRange) || 1;
  mountState.reconnectTimeoutRange =
    (mountState.reconnectTimeoutRange + 5) % maxReconnectTimeout;
  return timeout;
}

function LazyPromise() {
  this.promise = new Promise((resolve, reject) => {
    this.resolve = resolve;
    this.reject = reject;
  });
}
