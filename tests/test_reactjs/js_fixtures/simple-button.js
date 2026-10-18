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

export function SimpleButton(props) {
  return h(
    "button",
    {
      id: props.id,
      onClick(event) {
        props.onClick({ data: props.eventResponseData });
      },
    },
    "simple button",
  );
}
