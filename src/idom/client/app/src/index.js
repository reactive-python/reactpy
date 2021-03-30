import { mountLayout } from "idom-client-react";
import { unmountComponentAtNode } from "react-dom";

const maxReconnectTimeout = 45;
const initialReconnectTimeoutRange = 5;

const userPackages = import("./user-packages.js").then((module) => {
  for (const pkgName in module.default) {
    module.default[pkgName].then((pkg) => {
      console.log(`Loaded module '${pkgName}'`);
    });
  }
});

function defaultWebSocketEndpoint() {
  const uri = document.location.hostname + ":" + document.location.port;
  const url = (uri + document.location.pathname).split("/").slice(0, -1);
  url[url.length - 1] = "stream";
  const secure = document.location.protocol === "https:";

  let protocol;
  if (secure) {
    protocol = "wss:";
  } else {
    protocol = "ws:";
  }

  return protocol + "//" + url.join("/") + "?" + queryParams.user.toString();
}

export function mountLayoutWithWebSocket(
  element,
  endpoint = defaultWebSocketEndpoint(),
  importSourceURL = "./",
  mountState = {
    everMounted: false,
    reconnectAttempts: 0,
    reconnectTimeoutRange: initialReconnectTimeoutRange,
  }
) {
  const socket = new WebSocket(endpoint);

  let resolveUpdateHook = null;
  let rejectUpdateHook = null;
  const updateHookPromise = new Promise((resolve, reject) => {
    resolveUpdateHook = resolve;
    rejectUpdateHook = reject;
  });

  socket.onopen = (event) => {
    console.log(`Connected.`);
    if (mountState.everMounted) {
      unmountComponentAtNode(element);
    }
    mountLayout(
      element,
      (updateHook) => resolveUpdateHook(updateHook),
      (event) => socket.send(JSON.stringify(event)),
      importSourceURL
    );
    _setOpenMountState(mountState);
  };

  socket.onmessage = (event) => {
    updateHookPromise.then((update) => {
      const [pathPrefix, patch] = JSON.parse(event.data);
      update(pathPrefix, patch);
    });
  };

  socket.onclose = (event) => {
    if (!shouldReconnect()) {
      console.log(`Connection lost.`);
      return;
    }
    const reconnectTimeout = _nextReconnectTimeout(mountState);
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
  mountState.reconnectTimeoutRange = initialReconnectTimeoutRange;
}

function _nextReconnectTimeout(mountState) {
  const timeout = Math.floor(Math.random() * mountState.reconnectTimeoutRange);
  mountState.reconnectTimeoutRange =
    (mountState.reconnectTimeoutRange + 5) % maxReconnectTimeout;
  if (mountState.reconnectAttempts == 3) {
    window.alert(
      "Server connection was lost. Attempts to reconnect are being made in the background."
    );
  }
  return timeout;
}

function shouldReconnect() {
  return queryParams.reserved.get("noReconnect") === null;
}

const queryParams = (() => {
  const reservedParams = new URLSearchParams();
  const userParams = new URLSearchParams(window.location.search);

  const reservedParamNames = ["noReconnect"];
  reservedParamNames.forEach((name) => {
    const value = userParams.get(name);
    if (value !== null) {
      reservedParams.append(name, userParams.get(name));
      userParams.delete(name);
    }
  });

  return {
    reserved: reservedParams,
    user: userParams,
  };
})();
