# SQL Query Builder Plugin

A SQL query builder plugin for OpenAI MCP Extensions. Demonstrates table browsing, column selection, saved queries, and form elicitation.

## Features

- **Global & Thread Entrypoints** — Open the query builder from the sidebar or beside a conversation
- **Table Browser** — List tables, inspect schemas, and search by name or column
- **Column Picker** — Multi-select columns with thumbnails via form elicitation
- **Saved Queries** — Browse pre-built SQL queries
- **Query Review** — Form with patterns, enums, and numeric validation
- **Settings** — Default schema, row limit, result format, and timing display
- **Mentions** — Search tables from the composer

## Build

```sh
pnpm install
pnpm build
```

## Run

```sh
node ./dist/server.js
```
