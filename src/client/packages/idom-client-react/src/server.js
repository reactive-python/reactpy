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
    ).catch(() => {
      console.error("Import failed");
    });

  mountLayoutWithWebSocket(
    element,
    serverInfo.path.stream,
    loadImportSource,
    maxReconnectTimeout
  );
}

export function LayoutServerInfo({ host, port, query, secure }) {
  const wsProtocol = "ws" + (secure ? "s" : "");
  const httpProtocol = "http" + (secure ? "s" : "");

  const uri = host + ":" + port;
  const path = new URL(document.baseURI).pathname;
  const url = uri + path;

  const wsBaseUrl = wsProtocol + "://" + url;
  const httpBaseUrl = httpProtocol + "://" + url;

  if (query) {
    query = "?" + query;
  } else {
    query = "";
  }

  this.path = {
    stream: wsBaseUrl + "/_stream" + query,
    module: (source) => httpBaseUrl + `/modules/${source}`,
  };
}
