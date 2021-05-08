import react from "./react.js";

export function SimpleButton(props) {
  return react.createElement(
    "button",
    {
      id: props.id,
      onClick(event) {
        props.onClick({ data: props.eventResponseData });
      },
    },
    "simple button"
  );
}
