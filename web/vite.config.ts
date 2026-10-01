import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

// 1 つの HTML にまとめる（Artifact として公開できるように）
export default defineConfig({
  plugins: [react(), viteSingleFile()],
});
