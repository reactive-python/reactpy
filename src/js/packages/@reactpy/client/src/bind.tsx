import * as preact from "preact";

export async function infer_bind_from_environment() {
  try {
    // @ts-ignore
    const React = await import("react");
    // @ts-ignore
    const ReactDOM = await import("react-dom/client");

    console.log(
      "ReactPy detected 'ReactJS' to bind your JavaScript components.",
    );
    return (node: HTMLElement) => reactjs_bind(node, React, ReactDOM);
  } catch {
    console.debug(
      "ReactPy did not detect a component binding function or a suitable 'importmap'. Using ReactPy's internal framework (Preact) to bind your JavaScript components.",
    );
    return (node: HTMLElement) => local_preact_bind(node);
  }
}

function local_preact_bind(node: HTMLElement) {
  return {
    create: (type: any, props: any, children?: any[]) =>
      preact.createElement(type, props, ...(children || [])),
    render: (element: any) => {
      preact.render(element, node);
    },
    unmount: () => preact.render(null, node),
  };
}

const roots = new WeakMap<HTMLElement, any>();

function reactjs_bind(node: HTMLElement, React: any, ReactDOM: any) {
  let root: any = null;
  return {
    create: (type: any, props: any, children?: any[]) =>
      React.createElement(type, props, ...(children || [])),
    render: (element: any) => {
      if (!root) {
        if (!roots.get(node)) {
          root = ReactDOM.createRoot(node);
          roots.set(node, root);
        } else {
          root = roots.get(node);
        }
      }

      root.render(element);
    },
    unmount: () => {
      if (root) {
        root.unmount();
        if (roots.get(node) === root) {
          roots.delete(node);
        }
        root = null;
      }
    },
  };
}
