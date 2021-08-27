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

export function bind(node, config, sourceInfo) {
  return {
    render: (component, props, children) =>
      ReactDOM.render(
        createElement(config, sourceInfo, component, props, children),
        node
      ),
    unmount: () => ReactDOM.unmountComponentAtNode(node),
  };
}

function createElement(config, sourceInfo, component, props, children) {
  return React.createElement(
    LayoutConfigContext.Provider,
    { value: config },
    React.createElement(
      component,
      props,
      ...createChildren(config, sourceInfo, children)
    )
  );
}

function createChildren(config, sourceInfo, children) {
  if (!children) {
    return [];
  }
  return children.map((child) => {
    if (typeof child == "string") {
      return child;
    } else if (child.importSource) {
      return createElementFromThisImportSource(config, sourceInfo, child);
    } else {
      return React.createElement(Element, { model: child });
    }
  });
}

function createElementFromThisImportSource(config, sourceInfo, model) {
  if (
    model.importSource.source != sourceInfo.source ||
    model.importSource.sourceType != sourceInfo.sourceType
  ) {
    console.error(
      `Cannot create ${model.tagName} from different import source ` +
        `${model.importSource.source} (type: ${model.importSource.sourceType})`
    );
    return React.createElement("pre", {}, "error");
  }
  return React.createElement(
    ThisImportSource[model.tagName],
    elementAttributes(model, (event) => {
      event.data = event.data.filter((value) => {
        try {
          JSON.stringify(value);
        } catch (err) {
          console.error(
            `Failed to serialize some event data for ${model.tagName}`
          );
          return false;
        }
        return true;
      });
      config.sendEvent(event);
    }),
    ...createChildren(config, sourceInfo, model.children)
  );
}
