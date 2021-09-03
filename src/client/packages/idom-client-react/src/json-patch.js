import React from "react";
import jsonpatch from "fast-json-patch";

export function useJsonPatchCallback(initial) {
  const doc = React.useRef(initial);
  const forceUpdate = useForceUpdate();

  const applyPatch = React.useCallback(
    (path, patch) => {
      if (!path) {
        // We CANNOT mutate the part of the document because React checks some
        // attributes of the model (e.g. model.attributes.style is checked for
        // identity).
        doc.current = applyNonMutativePatch(doc.current, patch, false, false, true);
      } else {
        // We CAN mutate the document here though because we know that nothing above
        // The patch `path` is changing. Thus, maintaining the identity for that section
        // of the model is accurate.
        applyMutativePatch(doc.current, [
          {
            op: "replace",
            path: path,
            // We CANNOT mutate the part of the document where the actual patch is being
            // applied. Instead we create a copy because React checks some attributes of
            // the model (e.g. model.attributes.style is checked for identity). The part
            // of the document above the `path` can be mutated though because we know it
            // has not changed.
            value: applyNonMutativePatch(
              jsonpatch.getValueByPointer(doc.current, path),
              patch
            ),
          },
        ]);
      }
      forceUpdate();
    },
    [doc]
  );

  return [doc.current, applyPatch];
}

function applyNonMutativePatch(doc, patch) {
  return jsonpatch.applyPatch(doc, patch, false, false, true).newDocument;
}

function applyMutativePatch(doc, patch) {
  jsonpatch.applyPatch(doc, patch, false, true, true).newDocument;
}

function useForceUpdate() {
  const [, updateState] = React.useState();
  return React.useCallback(() => updateState({}), []);
}
