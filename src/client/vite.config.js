import { defineConfig } from "vite";

export default defineConfig({
  build: { outDir: "../reactpy/_client", emptyOutDir: true },
  resolve: {
    alias: {
      react: "preact/compat",
      "react-dom": "preact/compat",
    },
  },
  base: "/_reactpy",
});
