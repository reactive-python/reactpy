import * as React from "react";
import * as ReactTestUtils from "react-dom/test-utils.js";

export function render(Tag, props = {}) {
  const container = window.document.querySelector("main");
  const component = React.h(Tag, props);
  React.render(component, container);
  return { container, component };
}

export async function fire(elem, event, details) {
  await ReactTestUtils.act(() => {
    let evt = new window.Event(event, details);
    elem.dispatchEvent(evt);
  });
}
