import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const rootDir = fileURLToPath(new URL("./", import.meta.url));

export default defineConfig({
  root: rootDir,
  resolve: {
    alias: {
      "@": rootDir,
    },
  },
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    css: true,
  },
});
