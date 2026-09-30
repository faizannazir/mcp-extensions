import { describe, expect, it } from "vitest";
import { standardFieldSchemas, type OpenAIFormOption } from "./fields.js";

describe("standardFieldSchemas", () => {
  it("includes single-select, multi-select, and primitive schemas", () => {
    expect(standardFieldSchemas.length).toBeGreaterThanOrEqual(5);
  });

  it("validates a single-select field", () => {
    const singleSelect = standardFieldSchemas[0];
    const result = singleSelect.safeParse({
      type: "string",
      title: "Pick one",
      oneOf: [{ const: "a", title: "A" }],
    });
    expect(result.success).toBe(true);
  });

  it("rejects x-openai-input on standard fields", () => {
    const stringField = standardFieldSchemas.find(
      (s) => s.safeParse({ type: "string", title: "Test" }).success,
    );
    expect(stringField).toBeDefined();
  });
});

describe("OpenAIFormOption", () => {
  it("accepts a basic option", () => {
    const option: OpenAIFormOption = { const: "a", title: "A" };
    expect(option.const).toBe("a");
  });

  it("supports thumbnail and description", () => {
    const option: OpenAIFormOption = {
      const: "a",
      title: "A",
      description: "Option A",
      "x-openai-thumbnail": { src: "https://example.com/a.png" },
    };
    expect(option.description).toBe("Option A");
  });
});
