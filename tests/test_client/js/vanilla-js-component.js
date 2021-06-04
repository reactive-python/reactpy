export function mount(element, component, props) {
  component(element, props);
  incrAttribute(element, "mountCount");
  return () => {
    incrAttribute(element, "unmountCount");
    while (element.firstChild) {
      element.removeChild(element.lastChild);
    }
  };
}

export function ShowText(element, props) {
  const innerEl = document.createElement("h1");
  innerEl.setAttribute("id", props.id);
  innerEl.appendChild(document.createTextNode(props.text));
  element.appendChild(innerEl);
}

function incrAttribute(element, attribute) {
  const current = element.getAttribute(attribute);
  if (!current) {
    element.setAttribute(attribute, 1);
  } else {
    element.setAttribute(attribute, parseInt(current) + 1);
  }
}
