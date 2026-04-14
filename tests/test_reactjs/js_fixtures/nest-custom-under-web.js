import React from "react"
import ReactDOM from "react-dom/client"

export function Container({ children }) {
  return React.createElement("div", { id: "container" }, children)
}

export function bind(node, config) {
  const root = ReactDOM.createRoot(node);
  return {
    create: (type, props, children) =>
      React.createElement(type, props, children),
    render: (element) => root.render(element, node),
    unmount: () => root.unmount()
  };
}
