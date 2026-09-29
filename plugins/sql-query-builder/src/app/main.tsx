import { createRoot } from "react-dom/client";
import { OpenAIExtensions } from "@openai/mcp-extensions/app";
import { App } from "@modelcontextprotocol/ext-apps";

const app = new App();
const openai = new OpenAIExtensions(app);

function SqlQueryBuilder() {
  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <h1 className="text-lg font-semibold">SQL Query Builder</h1>
      <p className="text-sm opacity-70">
        Build and run SQL queries with table schema inspection, column selection, and saved queries.
      </p>
      <div className="grid gap-3">
        <div className="rounded-lg border p-3">
          <h2 className="text-sm font-medium">Features</h2>
          <ul className="mt-1 list-inside list-disc text-sm opacity-70">
            <li>Table browser with schema inspection</li>
            <li>Column picker with thumbnails</li>
            <li>Saved query library</li>
            <li>Query review form</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById("root")!);
root.render(<SqlQueryBuilder />);
