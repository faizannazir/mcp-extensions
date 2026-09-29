import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type PluginOption } from "vite";

export default defineConfig({
  build: {
    emptyOutDir: true,
    outDir: "dist",
    rolldownOptions: {
      output: {
        assetFileNames: "views/[name][extname]",
        chunkFileNames: "views/[name].js",
        entryFileNames: "views/[name].js",
      },
    },
  },
  plugins: [tailwindcss(), react() as PluginOption],
});
