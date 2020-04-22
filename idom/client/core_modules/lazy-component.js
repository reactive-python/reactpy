import htm from "../web_modules/htm.js";
import React, { lazy } from "../web_modules/react.js";

const html = htm.bind(React.createElement);

function lazyComponent(model) {
  return lazy(() => {
    return eval(`import('${model.importSource.source}')`).then(
      (pkg) => {
        pkg = pkg.default ? pkg.default : pkg;
        const cmpt = model.tagName ? getPathProperty(pkg, model.tagName) : pkg;
        return { default: cmpt };
      },
      (error) => {
        if (!error.stack) {
          throw error;
        } else {
          console.log(error);
          return {
            default: function Catch() {
              return html`
                <pre>
                  <h1>Error</h1>
                  <code>${[error.stack, error.message]}</code>
                </pre
                >
              `;
            },
          };
        }
      }
    );
  });
}

function getPathProperty(obj, prop) {
  // properties may be dot seperated strings
  const path = prop.split(".");
  const firstProp = path.shift();
  let value = obj[firstProp];
  for (let i = 0; i < path.length; i++) {
    value = value[path[i]];
  }
  return value;
}

export default lazyComponent;
