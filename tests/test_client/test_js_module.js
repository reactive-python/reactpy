import React from "./react.js";
import htm from "./htm.js";

const html = htm.bind(React.createElement);

export function TestButton(props) {
  return html`<button
    id=${props.id}
    onClick=${(event) => props.onClick({ data: props.eventResponseData })}
  >
    test button
  </button>`;
}
