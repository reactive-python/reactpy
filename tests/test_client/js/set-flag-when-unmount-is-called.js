export function render(element, component, props) {
  if (element.firstChild) {
    element.removeChild(element.firstChild);
  }
  element.appendChild(component(props));
}

export function unmount(element) {
  // We add an element to the document.body to indicate that this function was called.
  // Thus allowing Selenium to see communicate to server-side code that this effect
  // did indeed occur.
  const unmountFlag = document.createElement("h1");
  unmountFlag.setAttribute("id", "unmount-flag");
  document.body.appendChild(unmountFlag);
  element.innerHTML = "";
}

export function SomeComponent(props) {
  const element = document.createElement("h1");
  element.appendChild(document.createTextNode(props.text));
  element.setAttribute("id", props.id);
  return element;
}
