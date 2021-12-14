import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import replace from "@rollup/plugin-replace";

export default {
  input: "src/index.js",
  output: {
    file: "../_static/custom.js",
    format: "esm",
  },
  plugins: [
    resolve(),
    commonjs(),
    replace({
      "process.env.NODE_ENV": JSON.stringify("production"),
      preventAssignment: true,
    }),
  ],
  onwarn: function (warning) {
    if (warning.code === "THIS_IS_UNDEFINED") {
      // skip warning where `this` is undefined at the top level of a module
      return;
    }
    console.warn(warning.message);
  },
};
