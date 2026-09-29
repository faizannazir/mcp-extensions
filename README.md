# OpenAI MCP Extensions

OpenAI MCP Extensions adds ChatGPT-specific capabilities to MCP so developers can build plugins that feel like native, first-class features.

> [!IMPORTANT]
> This library is currently in alpha. APIs may change, be added, or be removed without warning.

## Showcase

All examples below use the Bits & Bolts plugin, which you can try by [installing the plugin](#0-try-it-out).

### [Sidebar entrypoints](docs/spec.md#mcp-app-entrypoints)

Allow users to access your app from the sidebar.

![Opening an MCP App from the sidebar](resources/sidebar-entrypoint.gif)

### [File extension handlers](docs/spec.md#file-extension-entrypoint)

Render custom file viewers when users open a supported file type.

![Opening a CAD file in a custom file viewer](resources/file-viewer.gif)

### [Composer mentions](docs/spec.md#composer-at-mentions)

Let users search your plugin’s resources from the composer and add references to a message.

![Searching for a CAD part with composer mentions](resources/composer-mentions.gif)

### [Extended forms](docs/spec.md#openai-form-elicitation)

Let users select a CAD part using thumbnail choices.

![Selecting a CAD part in a Bits & Bolts form](resources/image-picker.gif)

## Get started

### 0. Try it out

Install the Bits & Bolts plugin:

1. Make sure [Node.js 22 or newer](https://nodejs.org/en/download) is installed.
2. Download and extract the [latest marketplace](https://github.com/OpenAI-Early-Access/mcp-extensions/releases/download/marketplace-latest/marketplace.zip), then install from the extracted directory. The download requires access to this repository.

   ```sh
   cd mcp-extensions-early-access
   codex plugin marketplace add .
   codex plugin add bits-and-bolts@mcp-extensions-early-access
   ```

3. Fully quit and reopen the Codex desktop app.
4. Select **Bits & Bolts** in the sidebar to open the **Parts Library**.

   ![Bits & Bolts selected in the sidebar with the Parts Library open](resources/01-global-library.png)

### 1. Create a plugin

Read the [plugin documentation](https://developers.openai.com/codex/build-plugins) about how to create a plugin. Once you have a plugin…

### 2. Add the SDKs to your MCP server

Follow the SDK installation instructions for the current source:

- [TypeScript](typescript/README.md#installation): `@openai/mcp-extensions` for MCP servers and Apps.
- [Python](python/README.md#installation): `openai-mcp-extensions` for MCP servers.

### 3. Explore supported extensions

Read the [spec](docs/spec.md) to learn more about supported extensions.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
