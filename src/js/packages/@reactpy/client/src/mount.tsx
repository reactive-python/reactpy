import { default as React, default as ReactDOM } from "preact/compat";
import { ReactPyClient } from "./client";
import { Layout } from "./components";
import { MountProps } from "./types";

export function mountReactPy(props: MountProps) {
  // WebSocket route for component rendering
  const wsProtocol = `ws${window.location.protocol === "https:" ? "s" : ""}:`;
  const wsOrigin = `${wsProtocol}//${window.location.host}`;
  const componentUrl = new URL(`${wsOrigin}/${props.pathPrefix}/`);

  // Embed the initial HTTP path into the WebSocket URL
  componentUrl.searchParams.append("http_pathname", window.location.pathname);
  if (window.location.search) {
    componentUrl.searchParams.append("http_search", window.location.search);
  }

  // Configure a new ReactPy client
  const client = new ReactPyClient({
    urls: {
      componentUrl: componentUrl,
      query: document.location.search,
      jsModules: `${window.location.origin}/${props.pathPrefix}/modules/`,
    },
    reconnectOptions: {
      interval: props.reconnectInterval || 750,
      maxInterval: props.reconnectMaxInterval || 60000,
      backoffMultiplier: props.reconnectBackoffMultiplier || 1.25,
      maxRetries: props.reconnectMaxRetries || 150,
    },
    mountElement: props.mountElement,
  });

  // Start rendering the component
  // eslint-disable-next-line react/no-deprecated
  ReactDOM.render(<Layout client={client} />, props.mountElement);
}
