import React from "https://esm.sh/v135/react@19.0"
import ReactDOM from "https://esm.sh/v135/react-dom@19.0/client"
import * as ReactIs from "https://esm.sh/v135/react-is@19.0"
import {InputGroup, Form} from "https://esm.sh/v135/react-bootstrap@2.10.2?deps=react@19.0,react-dom@19.0,react-is@19.0&exports=InputGroup,Form";
export {InputGroup, Form};

export function bind(node, config) {
  const root = ReactDOM.createRoot(node);
  return {
    create: (type, props, children) => 
      React.createElement(type, props, ...children),
    render: (element) => root.render(element),
    unmount: () => root.unmount()
  };
}