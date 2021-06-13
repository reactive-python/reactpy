export * from "$CDN/$PACKAGE";

import { h, Component, render } from "$CDN/preact";
import htm from "$CDN/htm";

const html = htm.bind(h);

export { h as createElement, render as renderElement };

export function unmountElement(container) {
  preactRender(null, container);
}
