import React from "https://esm.sh/v135/react@18.3.1"
import ReactDOM from "https://esm.sh/v135/react-dom@18.3.1/client"
import GridLayout from "https://esm.sh/v135/react-grid-layout@1.5.0";
export {GridLayout};

export function bind(node, config) {
  const root = ReactDOM.createRoot(node);
  return {
    create: (type, props, children) =>
      React.createElement(type, props, children),
    render: (element) => root.render(element, node),
    unmount: () => root.unmount()
  };
}
