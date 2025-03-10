import React from "https://esm.sh/react@19.0"
import ReactDOM from "https://esm.sh/react-dom@19.0/client"
import GridLayout from "https://esm.sh/react-grid-layout@1.5.0";
export {GridLayout};

export function bind(node, config) {
  debugger;
  const root = ReactDOM.createRoot(node);
  return {
    create: (type, props, children) => 
      React.createElement(type, props, children),
    render: (element) => root.render(element, node),
    unmount: () => root.unmount()
  };
}
