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

export function Header1(props) {
  return h("h1", { id: props.id }, props.text);
}

export function Header2(props) {
  return h("h2", { id: props.id }, props.text);
}
