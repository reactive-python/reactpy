import React from "react";
import { render } from "react-dom";
import { Layout, SimpleReactPyClient } from "@reactpy/client";

export function mount(root: HTMLElement) {
  const client = new SimpleReactPyClient({
    serverLocation: {
      baseUrl: document.location.origin,
      routePath: document.location.pathname,
      queryString: document.location.search,
    },
  });
  render(<Layout client={client} />, root);
}
