import React from "https://esm.sh/react@19.0"
import ReactDOM from "https://esm.sh/react-dom@19.0/client"
import {Container} from "https://esm.sh/react-bootstrap@2.10.10/?deps=react@19.0,react-dom@19.0,react-is@19.0&exports=Container";
export {Container};

export function bind(node, config) {
  const root = ReactDOM.createRoot(node);
  return {
    create: (type, props, children) => 
      React.createElement(type, props, children),
    render: (element) => root.render(element, node),
    unmount: () => root.unmount()
  };
}