import { h, Component } from "../web_modules/preact.js";
import htm from "../web_modules/htm.js";
import { lazy } from "../web_modules/preact/compat.js";

const html = htm.bind(h);

function lazyComponent(model) {
  return lazy(() => {
    return eval(`import('${model.importSource.source}')`).then(
      (pkg) => {
        pkg = pkg.default ? pkg.default : pkg;
        const cmpt = model.tagName ? getPathProperty(pkg, model.tagName) : pkg;
        return {default: cmpt};
      },
      (error) => {
        function Catch() {
          return html`
            <pre>
              <code>${error.stack}</code>
            </pre
            >
          `;
        }
        return { default: Catch };
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
