import { createElement } from "react";
import { unmountComponentAtNode, render } from "react-dom";
import { Layout } from "./component.js";

export function mountLayout(mountElement, layoutProps) {
  render(createElement(Layout, layoutProps), mountElement);
}

export function mountLayoutWithWebSocket(
  element,
  endpoint,
  loadImportSource,
  maxReconnectTimeout = 0
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
  }
) {
  const socket = new WebSocket(endpoint);

  const updateHookPromise = new LazyPromise();

  socket.onopen = (event) => {
    console.log(`Connected.`);
    if (mountState.everMounted) {
      unmountComponentAtNode(element);
    }
    mountLayout(element, {
      loadImportSource,
      saveUpdateHook: updateHookPromise.resolve,
      sendEvent: (event) => socket.send(JSON.stringify(event)),
    });
    _setOpenMountState(mountState);
  };

  socket.onmessage = (event) => {
    const [pathPrefix, patch] = JSON.parse(event.data);
    updateHookPromise.promise.then((update) => update(pathPrefix, patch));
  };

  socket.onclose = (event) => {
    if (maxReconnectTimeout != 0) {
      console.log(`Connection lost.`);
      return;
    }
    const reconnectTimeout = _nextReconnectTimeout(
      maxReconnectTimeout,
      mountState
    );
    console.log(`Connection lost, reconnecting in ${reconnectTimeout} seconds`);
    setTimeout(function () {
      mountState.reconnectAttempts++;
      mountLayoutWithWebSocket(element, endpoint, importSourceURL, mountState);
    }, reconnectTimeout * 1000);
  };
}

function _setOpenMountState(mountState) {
  mountState.everMounted = true;
  mountState.reconnectAttempts = 0;
  mountState.reconnectTimeoutRange = 1;
}

function _nextReconnectTimeout(maxReconnectTimeout, mountState) {
  const timeout =
    Math.floor(Math.random() * mountState.reconnectTimeoutRange) || 1;
  mountState.reconnectTimeoutRange =
    (mountState.reconnectTimeoutRange + 5) % maxReconnectTimeout;
  if (mountState.reconnectAttempts == 4) {
    window.alert(
      "Server connection was lost. Attempts to reconnect are being made in the background."
    );
  }
  return timeout;
}

function LazyPromise() {
  this.promise = new Promise((resolve, reject) => {
    this.resolve = resolve;
    this.reject = reject;
  });
}
