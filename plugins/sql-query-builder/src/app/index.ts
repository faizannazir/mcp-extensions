import { App } from "@modelcontextprotocol/ext-apps";
import { OpenAIExtensions } from "@openai/mcp-extensions/app";

const app = new App();
const openai = new OpenAIExtensions(app);

export { app, openai };
