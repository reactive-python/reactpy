export function bind(node, config) {
  return {
    create: (type, props, children) => type(props),
    render: (element) => renderElement(element, node),
    unmount: () => unmountElement(node),
  };
}

export function renderElement(element, container) {
  if (container.firstChild) {
    container.removeChild(container.firstChild);
  }
  container.appendChild(element);
}

export function unmountElement(container) {
  // We add an element to the document.body to indicate that this function was called.
  // Thus allowing Selenium to see communicate to server-side code that this effect
  // did indeed occur.
  const unmountFlag = document.createElement("h1");
  unmountFlag.setAttribute("id", "unmount-flag");
  document.body.appendChild(unmountFlag);
  container.innerHTML = "";
}

export function SomeComponent(props) {
  const element = document.createElement("h1");
  element.appendChild(document.createTextNode(props.text));
  element.setAttribute("id", props.id);
  return element;
}
