import React from "react";
import ReactDOM from "react-dom";
import { mountLayoutWithWebSocket } from "./mount.js";

export function mountWithLayoutServer(
  element,
  serverInfo,
  maxReconnectTimeout
) {
  const loadImportSource = (source, sourceType) =>
    import(
      sourceType == "NAME" ? serverInfo.path.module(source) : source
    ).catch((error) => {
      // Added a catch to silence a build warning caller so we just re-throw.
      // The caller is actually responsible for catching this error.
      throw error;
    });

  mountLayoutWithWebSocket(
    element,
    serverInfo.path.stream,
    loadImportSource,
    maxReconnectTimeout
  );
}

export function LayoutServerInfo({ host, port, path, query, secure }) {
  const wsProtocol = "ws" + (secure ? "s" : "");
  const httpProtocol = "http" + (secure ? "s" : "");

  let url = host + ":" + port + (path || new URL(document.baseURI).pathname);

  if (url.endsWith("/")) {
    url = url.slice(0, -1);
  }

  const wsBaseUrl = wsProtocol + "://" + url;
  const httpBaseUrl = httpProtocol + "://" + url;

  if (query) {
    query = "?" + query;
  } else {
    query = "";
  }

  this.path = {
    stream: wsBaseUrl + "/_api/stream" + query,
    module: (source) => httpBaseUrl + `/_api/modules/${source}`,
  };
}
