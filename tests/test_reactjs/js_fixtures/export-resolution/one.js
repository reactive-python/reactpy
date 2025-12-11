export { one as One };
// use ../ just to check that it works
export * from "../export-resolution/two.js";
// this default should not be exported by the * re-export in index.js
export default 0;
