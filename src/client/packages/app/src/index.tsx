import React from "react";
import { render } from "react-dom";
import { Layout, SimpleReactPyServer } from "@reactpy/client";

export function mount(root: HTMLElement) {
  const server = new SimpleReactPyServer({
    serverApi: {
      baseUrl: document.location.origin,
      routePath: document.location.pathname,
      queryString: document.location.search,
    },
  });
  render(<Layout server={server} />, root);
}
