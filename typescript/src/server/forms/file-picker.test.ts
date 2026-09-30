import { describe, expect, it } from "vitest";
import { OpenAIFileFormFieldSchema, isValidFileSelection } from "./file-picker.js";

describe("OpenAIFileFormFieldSchema", () => {
  it("accepts a single-select file field", () => {
    const field = {
      type: "string",
      title: "File",
      format: "uri",
      "x-openai-input": {
        type: "resource",
        options: [{ uri: "file:///test.txt", name: "test.txt" }],
      },
    };
    expect(OpenAIFileFormFieldSchema.safeParse(field).success).toBe(true);
  });

  it("accepts a multi-select file field", () => {
    const field = {
      type: "array",
      title: "Files",
      items: { type: "string", format: "uri" },
      "x-openai-input": {
        type: "resource",
        selection: "explicit",
        options: [{ uri: "file:///a.txt", name: "a.txt" }],
      },
    };
    expect(OpenAIFileFormFieldSchema.safeParse(field).success).toBe(true);
  });

  it("rejects implicit selection with a default", () => {
    const field = {
      type: "array",
      title: "Files",
      items: { type: "string", format: "uri" },
      "x-openai-input": {
        type: "resource",
        selection: "implicit",
        options: [{ uri: "file:///a.txt", name: "a.txt" }],
      },
      default: ["file:///a.txt"],
    };
    expect(OpenAIFileFormFieldSchema.safeParse(field).success).toBe(false);
  });

  it("rejects defaults not in options", () => {
    const field = {
      type: "string",
      title: "File",
      format: "uri",
      "x-openai-input": {
        type: "resource",
        options: [{ uri: "file:///a.txt", name: "a.txt" }],
      },
      default: "file:///b.txt",
    };
    expect(OpenAIFileFormFieldSchema.safeParse(field).success).toBe(false);
  });
});

describe("isValidFileSelection", () => {
  it("returns true for implicit selection", () => {
    const input = {
      type: "resource" as const,
      selection: "implicit" as const,
      options: [],
    };
    expect(isValidFileSelection(input, "file:///anything.txt")).toBe(true);
  });

  it("returns true when user uploads are allowed", () => {
    const input = {
      type: "resource" as const,
      options: [],
      userOptions: { kind: "file" as const },
    };
    expect(isValidFileSelection(input, "file:///upload.txt")).toBe(true);
  });

  it("returns false for URIs not in options", () => {
    const input = {
      type: "resource" as const,
      options: [{ uri: "file:///a.txt", name: "a.txt" }],
    };
    expect(isValidFileSelection(input, "file:///b.txt")).toBe(false);
  });
});
