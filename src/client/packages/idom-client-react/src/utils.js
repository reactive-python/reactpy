import React from "react";
import jsonpatch from "fast-json-patch";

export function useJsonPatchCallback(initial) {
  const model = React.useRef(initial);
  const forceUpdate = useForceUpdate();

  const applyPatch = React.useCallback(
    (pathPrefix, patch) => {
      if (pathPrefix) {
        patch = patch.map((op) =>
          Object.assign({}, op, { path: pathPrefix + op.path })
        );
      }
      // Always return a newDocument because React checks some attributes of the model
      // (e.g. model.attributes.style is checked for identity)
      model.current = jsonpatch.applyPatch(
        model.current,
        patch,
        false,
        false,
        true
      ).newDocument;
      forceUpdate();
    },
    [model]
  );

  return [model.current, applyPatch];
}

function useForceUpdate() {
  const [, updateState] = React.useState();
  return React.useCallback(() => updateState({}), []);
}
