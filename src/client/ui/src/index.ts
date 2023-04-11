import { mount, SimpleReactPyClient } from "@reactpy/client";

export function app(element: HTMLElement) {
  const client = new SimpleReactPyClient({
    serverLocation: {
      url: document.location.origin,
      route: document.location.pathname,
      query: document.location.search,
    },
  });
  mount(element, client);
}
