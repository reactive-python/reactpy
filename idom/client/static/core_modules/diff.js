import DiffMatchPatch from "../web_modules/diff-match-patch.js";

const diffMatchPatch = new DiffMatchPatch();

export default (patchText, textToPatch) =>
  diffMatchPatch.patch_apply(
    diffMatchPatch.patch_fromText(patchText),
    textToPatch
  )[0];
