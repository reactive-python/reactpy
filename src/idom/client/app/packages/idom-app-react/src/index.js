import { mountLayoutWithWebSocket } from "idom-client-react";
import { unmountComponentAtNode } from "react-dom";

// imported so static analysis knows to pick up files linked by user-packages.js
import("./user-packages.js").then((module) => {
  for (const pkgName in module.default) {
    module.default[pkgName].then((pkg) => {
      console.log(`Loaded module '${pkgName}'`);
    });
  }
});

export function mount(mountPoint) {
  mountLayoutWithWebSocket(
    mountPoint,
    getWebSocketEndpoint(),
    loadImportSource,
    shouldReconnect() ? 45 : 0
  );
}

function getWebSocketEndpoint() {
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

function loadImportSource(source, sourceType) {
  return import(sourceType == "NAME" ? `./${source}.js` : source);
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
