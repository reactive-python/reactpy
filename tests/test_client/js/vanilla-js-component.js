export function mount(element, component, props, children) {
  component(element, props, children);
}

export function SetInnerHtml(element, props, children) {
  element.innerHTML = props.innerHTML;
}
