export * from "$CDN/$PACKAGE";

import * as React from "$CDN/react";
import * as ReactDOM from "$CDN/react-dom";
import { LayoutConfigContext, elementChildren } from "$CDN/idom-client-react";

export function bind(node, config) {
  return {
    render: (component, props, children) =>
      ReactDOM.render(createElement(config, component, props, children), node),
    unmount: () => ReactDOM.unmountComponentAtNode(node),
  };
}

function createElement(config, component, props, children) {
  return React.createElement(
    LayoutConfigContext.Provider,
    { value: config },
    React.createElement(
      component, props, ...elementChildren(children)
    )
  )
}
