// The bind() export tells the client how to put nodes on screen. It receives
// the container element the client owns and a config object carrying
// sendMessage/onMessage, and must hand back create/render/unmount.
export function bind(node, config) {
  return {
    create: (component, props, children) => {
      const el = document.createElement("span");
      el.className = props.tone || "default";
      el.textContent = props.label + ": " + (children || []).join("");
      el.addEventListener("click", () => {
        if (props.onPick) {
          props.onPick({ label: props.label });
        }
      });
      node.appendChild(el);
      return el;
    },
    render: (el) => {
      node.innerHTML = "";
      node.appendChild(el);
    },
    unmount: () => {
      node.innerHTML = "";
    },
  };
}

// One export per component you intend to register by name.
export function Badge(props, children) {
  return { props, children };
}
