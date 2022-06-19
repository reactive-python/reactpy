export * from "$CDN/$PACKAGE";

import * as React from "$CDN/react$VERSION";
import * as ReactDOM from "$CDN/react-dom$VERSION";

export default ({ children, ...props }) => {
  const [{ component }, setComponent] = React.useState({});
  React.useEffect(() => {
    import("$CDN/$PACKAGE").then((module) => {
      // dynamically load the default export since we don't know if it's exported.
      setComponent({ component: module.default });
    });
  });
  return component
    ? React.createElement(component, props, ...(children || []))
    : null;
};

export function bind(node, config) {
  return {
    create: (component, props, children) =>
      React.createElement(component, wrapEventHandlers(props), ...children),
    render: (element) => ReactDOM.render(element, node),
    unmount: () => ReactDOM.unmountComponentAtNode(node),
  };
}

function wrapEventHandlers(props) {
  const newProps = Object.assign({}, props);
  for (const [key, value] of Object.entries(props)) {
    if (typeof value === "function") {
      newProps[key] = makeJsonSafeEventHandler(value);
    }
  }
  return newProps;
}

function makeJsonSafeEventHandler(oldHandler) {
  // Since we can't really know what the event handlers get passed we have to check if
  // they are JSON serializable or not. We can allow normal synthetic events to pass
  // through since the original handler already knows how to serialize those for us.
  return function safeEventHandler() {
    oldHandler(
      ...Array.from(arguments).filter((value) => {
        if (typeof value === "object" && value.nativeEvent) {
          // this is probably a standard React synthetic event
          return true;
        } else {
          try {
            JSON.stringify(value);
          } catch (err) {
            console.error("Failed to serialize some event data");
            return false;
          }
          return true;
        }
      })
    );
  };
}
