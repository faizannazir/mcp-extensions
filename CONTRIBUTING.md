# Contributing

Thanks for your interest in contributing to OpenAI MCP Extensions!

## Development Setup

This is a pnpm monorepo with three packages:

- `typescript/` — TypeScript SDK (`@openai/mcp-extensions`)
- `python/` — Python SDK (`openai-mcp-extensions`)
- `plugins/` — Example plugins

### Prerequisites

- Node.js >= 22
- pnpm >= 11
- Python >= 3.10

### Install

```sh
pnpm install
```

### Common Commands

```sh
# TypeScript SDK
cd typescript && pnpm build && pnpm test

# Python SDK
cd python && python -m pytest tests/

# Lint
pnpm lint

# Typecheck all packages
pnpm typecheck
```

## Pull Requests

1. Fork the repository and create a branch from `main`.
2. Make your changes with clear commit messages.
3. Add or update tests for any behavior changes.
4. Ensure `pnpm lint` and `pnpm typecheck` pass.
5. Open a PR with a clear description of the change and its motivation.

## Code Style

- TypeScript: ESLint + Prettier (config at root)
- Python: Ruff + Pyright (config in `python/pyproject.toml`)

## Reporting Issues

Please use the issue templates in `.github/ISSUE_TEMPLATE/` when filing bugs or feature requests.
