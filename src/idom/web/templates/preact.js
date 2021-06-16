import { render } from "$CDN/preact";

export { h as createElement, render as renderElement } from "$CDN/preact";

export function unmountElement(container) {
  render(null, container);
}

export * from "$CDN/$PACKAGE";
