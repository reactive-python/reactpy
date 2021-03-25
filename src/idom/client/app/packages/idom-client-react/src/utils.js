import * as jsonpatch from "fast-json-patch";

export function applyPatchInplace(doc, path, patch) {
  if (!path) {
    jsonpatch.applyPatch(doc, patch);
  } else {
    jsonpatch.applyPatch(doc, [
      {
        op: "replace",
        path: path,
        value: jsonpatch.applyPatch(
          jsonpatch.getValueByPointer(doc, path),
          patch,
          false,
          false
        ).newDocument,
      },
    ]);
  }
}

export function getPathProperty(obj, prop) {
  // properties may be dot seperated strings
  const path = prop.split(".");
  const firstProp = path.shift();
  let value = obj[firstProp];
  for (let i = 0; i < path.length; i++) {
    value = value[path[i]];
  }
  return value;
}

export function joinUrl(base, tail) {
  return tail.startsWith("./")
    ? (base.endsWith("/") ? base.slice(0, -1) : base) + tail.slice(1)
    : tail;
}
