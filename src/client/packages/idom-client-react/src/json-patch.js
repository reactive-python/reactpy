import React from "react";

export function useJsonPatchCallback(initial) {
  const doc = React.useRef(initial);
  const forceUpdate = useForceUpdate();

  const applyPatch = React.useCallback(
    ({ path, new: newDoc }) => {
      if (!path) {
        doc.current = newDoc;
      } else {
        let value = doc.current;
        const pathParts = path
          .split("/")
          .map((pathPart) =>
            startsWithNumber(pathPart) ? Number(pathPart) : pathPart
          );
        const pathPrefix = pathParts.slice(0, -1);
        const pathLast = pathParts[pathParts.length - 1];
        for (const pathPart in pathPrefix) {
          value = value[pathPart];
        }
        value[pathLast] = newDoc;
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

function startsWithNumber(str) {
  return /^\d/.test(str);
}
