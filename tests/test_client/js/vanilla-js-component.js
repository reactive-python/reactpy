export function mount(element, component, props) {
  component(element, props);
}

export function SetInnerHtml(element, props) {
  element.innerHTML = props.innerHTML;
}
