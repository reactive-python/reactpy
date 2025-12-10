import { h } from "https://unpkg.com/preact?module";

export function GenericComponent(props) {
  return h("div", { id: props.id }, props.text);
}
