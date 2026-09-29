import { readFile } from "node:fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerCadServer } from "./register.js";
import { createLocalStore } from "./local-store.js";
const iconSvg = await readFile(
  new URL("../assets/icon.svg", import.meta.url),
  "utf8",
);
const server = new McpServer({
  name: "bits-and-bolts",
  title: "Bits & Bolts",
  version: "0.1.0",
  icons: [
    {
      src: "data:image/svg+xml," + encodeURIComponent(iconSvg),
      mimeType: "image/svg+xml",
    },
  ],
});
await registerCadServer({
  server,
  store: await createLocalStore(),
  html: await readFile(new URL("./app.html", import.meta.url), "utf8"),
  iconSvg,
  formats: ["stl", "3mf", "step", "stp"],
  wasm: await readFile(new URL("./occt-import-js.wasm", import.meta.url)),
  requestClient: () => server.server,
});
await server.connect(new StdioServerTransport());
