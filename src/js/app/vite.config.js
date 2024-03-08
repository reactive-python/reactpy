import { defineConfig } from "vite";

export default defineConfig({
  build: { emptyOutDir: true },
  resolve: {
    alias: {
      react: "preact/compat",
      "react-dom": "preact/compat",
    },
    preserveSymlinks: true,
  },
  base: "/_reactpy/",
});
