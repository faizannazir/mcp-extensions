import { describe, expect, it } from "vitest";
import {
  OpenAIFormSchema,
  OpenAIFormResultSchema,
  createOpenAIFormContentSchema,
} from "./schema.js";

describe("OpenAIFormSchema", () => {
  it("accepts a valid form schema", () => {
    const form = {
      type: "object" as const,
      properties: {
        name: { type: "string", title: "Name" },
      },
      required: ["name"],
    };
    expect(OpenAIFormSchema.safeParse(form).success).toBe(true);
  });

  it("rejects non-object types", () => {
    expect(OpenAIFormSchema.safeParse({ type: "string" }).success).toBe(false);
  });

  it("rejects properties with x-openai-input on non-file fields", () => {
    const form = {
      type: "object" as const,
      properties: {
        name: {
          type: "string",
          title: "Name",
          "x-openai-input": { type: "resource", options: [] },
        },
      },
    };
    expect(OpenAIFormSchema.safeParse(form).success).toBe(false);
  });
});

describe("OpenAIFormResultSchema", () => {
  it("accepts accept action with content", () => {
    const result = { action: "accept", content: { name: "test" } };
    expect(OpenAIFormResultSchema.safeParse(result).success).toBe(true);
  });

  it("accepts cancel action", () => {
    expect(OpenAIFormResultSchema.safeParse({ action: "cancel" }).success).toBe(true);
  });

  it("rejects invalid action", () => {
    expect(OpenAIFormResultSchema.safeParse({ action: "invalid" }).success).toBe(false);
  });
});

describe("createOpenAIFormContentSchema", () => {
  it("validates content against the form schema", () => {
    const form = OpenAIFormSchema.parse({
      type: "object",
      properties: {
        name: { type: "string", title: "Name", minLength: 1 },
        age: { type: "integer", title: "Age", minimum: 0 },
      },
      required: ["name"],
    });
    const schema = createOpenAIFormContentSchema(form);
    expect(schema.safeParse({ name: "Alice", age: 30 }).success).toBe(true);
    expect(schema.safeParse({ name: "" }).success).toBe(false);
    expect(schema.safeParse({ age: 30 }).success).toBe(false);
  });
});
