import React from "https://esm.sh/react@19.0"
import ReactDOM from "https://esm.sh/react-dom@19.0/client"
import Form from "https://esm.sh/react-bootstrap@2.10.9/Form";
export {Form};

export function bind(node, config) {
  const root = ReactDOM.createRoot(node);
  return {
    create: (type, props, children) => 
      React.createElement(type, props, children),
    render: (element) => root.render(element, node),
    unmount: () => root.unmount()
  };
}