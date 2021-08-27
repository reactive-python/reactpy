export * from "$CDN/$PACKAGE";
import * as ThisImportSource from "$CDN/$PACKAGE";

import * as React from "$CDN/react";
import * as ReactDOM from "$CDN/react-dom";
import {
  LayoutConfigContext,
  Element,
  elementAttributes,
  elementChildren,
} from "$CDN/idom-client-react";

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
    React.createElement(component, props, ...createChildren(children, config))
  );
}

function createChildren(children, config) {
  if (!children) {
    return [];
  }
  return children.map((child) => {
    if (typeof child == "string") {
      return child;
    } else if (child.importSource) {
      return createElementFromThisImportSource(child, config);
    } else {
      return React.createElement(Element, { model: child });
    }
  });
}

function createElementFromThisImportSource(model, config) {
  const Component = ThisImportSource[model.tagName];
  if (!Component) {
    console.error(
      `Cannot create ${model.tagName} from different import source ` +
        `${model.importSource.source} (type: ${model.importSource.sourceType})`
    );
  }
  return React.createElement(
    Component,
    elementAttributes(model, (event) => {
      event.data = event.data.filter(value => {
        try {
          JSON.stringify(value);
        } catch (err) {
          console.error(`Failed to serialize some event data for ${model.tagName}`)
          return false;
        }
        return true;
      })
      config.sendEvent(event);
    }),
    ...createChildren(model.children, config)
  );
}
