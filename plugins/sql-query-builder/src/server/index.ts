import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { registerSqlServer } from "./register.js";
import { createSqlStore } from "./store.js";

const iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.33"><ellipse cx="10" cy="5" rx="7" ry="3"/><path d="M3 5v10c0 1.66 3.13 3 7 3s7-1.34 7-3V5"/><path d="M3 10c0 1.66 3.13 3 7 3s7-1.34 7-3"/></svg>`;

const html = readFileSync(resolve(__dirname, "../dist/app.html"), "utf-8");

const server = new McpServer({
  name: "sql-query-builder",
  version: "0.1.0",
});

const store = createSqlStore();
registerSqlServer({ server, store, html, iconSvg });

export { server };
