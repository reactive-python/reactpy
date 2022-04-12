module.exports = {
  workspaceRoot: false,
  testOptions: { files: ["**/tests/**/*", "**/*.test.*"] },
  buildOptions: { out: "../idom/_client" },
  mount: { public: { url: "/", static: true } },
  optimize: { bundle: true, target: "es2018" },
  alias: {
    react: "preact/compat",
    "react-dom": "preact/compat",
  },
};
