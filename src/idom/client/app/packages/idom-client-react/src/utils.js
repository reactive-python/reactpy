import jsonpatch from "fast-json-patch";

export function applyPatchInplace(doc, pathPrefix, patch) {
  if (pathPrefix) {
    patch = patch.map((op) =>
      Object.assign({}, op, { path: pathPrefix + op.path })
    );
  }
  jsonpatch.applyPatch(doc, patch, false, true);
}

export function joinUrl(base, tail) {
  return tail.startsWith("./")
    ? (base.endsWith("/") ? base.slice(0, -1) : base) + tail.slice(1)
    : tail;
}
