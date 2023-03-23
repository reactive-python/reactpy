import { mount, SimpleReactPyClient } from "@reactpy/client";

export function app(element: HTMLElement) {
  mount(
    element,
    new SimpleReactPyClient({
      serverLocation: {
        url: document.location.host,
        route: document.location.pathname,
        query: document.location.search,
      },
    }),
  );
}
