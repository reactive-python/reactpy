import { mount, SimpleReactPyClient } from "@reactpy/client";

function app(element: HTMLElement) {
  const client = new SimpleReactPyClient({
    serverLocation: {
      url: document.location.origin,
      route: document.location.pathname,
      query: document.location.search,
    },
  });
  mount(element, client);
}

const element = document.getElementById("app");
if (element) {
  app(element);
} else {
  console.error("Element with id 'app' not found");
}
