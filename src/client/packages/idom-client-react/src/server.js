import React from "react";
import ReactDOM from "react-dom";
import { mountLayoutWithWebSocket } from "./mount.js";

export function mountWithLayoutServer(
  element,
  serverInfo,
  maxReconnectTimeout
) {
  const loadImportSource = (source, sourceType) =>
    import(sourceType == "NAME" ? serverInfo.path.module(source) : source);

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

  const uri = host + ":" + port;
  path = new URL(path, document.baseURI).pathname;
  const url = (uri + path).split("/").slice(0, -1).join("/");

  const wsBaseUrl = wsProtocol + "://" + url;
  const httpBaseUrl = httpProtocol + "://" + url;

  if (query) {
    query = "?" + query;
  } else {
    query = "";
  }

  this.path = {
    stream: wsBaseUrl + "/stream" + query,
    module: (source) => httpBaseUrl + `/modules/${source}`,
  };
}
