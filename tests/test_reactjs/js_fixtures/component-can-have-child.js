import { h, render } from "https://unpkg.com/preact?module";
import htm from "https://unpkg.com/htm?module";

const html = htm.bind(h);

export function bind(node, config) {
  return {
    create: (type, props, children) => h(type, props, ...children),
    render: (element) => render(element, node),
    unmount: () => render(null, node),
  };
}

// The intention here is that Child components are passed in here so we check that the
// children of "the-parent" are "child-1" through "child-N"
export function Parent(props) {
  return html`
    <div>
      <p>the parent</p>
      <ul id="the-parent">${props.children}</div>
    </div>
  `;
}

export function Child({ index }) {
  return html`<li id="child-${index}">child ${index}</li>`;
}
