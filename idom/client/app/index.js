import { mountLayout } from "idom-client-react";

export function mountLayoutWithWebSocket(element, endpoint, importSourceURL) {
  const ws = new WebSocket(endpoint || defaultWebSocketEndpoint());

  function saveUpdateHook(update) {
    ws.onmessage = (event) => {
      const [pathPrefix, patch] = JSON.parse(event.data);
      update(pathPrefix, patch);
    };
  }

  function sendCallback(event) {
    ws.send(JSON.stringify(event));
  }

  mountLayout(element, saveUpdateHook, sendCallback, importSourceURL || "./");
}

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

  return protocol + "//" + url.join("/") + window.location.search;
}
