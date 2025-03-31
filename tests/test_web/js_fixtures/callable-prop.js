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
export function Component(props) {
  var text = "DEFAULT";
  if (props.setText && typeof props.setText === "function") {
    text = props.setText("PREFIX TEXT: ");
  }
  return html`
    <div id="${props.id}">
    ${text}
    </div>
  `;
}
