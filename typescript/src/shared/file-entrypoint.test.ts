import { describe, expect, it } from "vitest";
import { OpenAIFileEntrypointInputSchema } from "./file-entrypoint.js";

describe("OpenAIFileEntrypointInputSchema", () => {
  it("accepts valid file entrypoint input", () => {
    const input = {
      file: { name: "test.txt", resourceUri: "file:///test.txt" },
    };
    expect(OpenAIFileEntrypointInputSchema.safeParse(input).success).toBe(true);
  });

  it("rejects empty file name", () => {
    const input = {
      file: { name: "", resourceUri: "file:///test.txt" },
    };
    expect(OpenAIFileEntrypointInputSchema.safeParse(input).success).toBe(false);
  });

  it("rejects blank resource URI", () => {
    const input = {
      file: { name: "test.txt", resourceUri: "  " },
    };
    expect(OpenAIFileEntrypointInputSchema.safeParse(input).success).toBe(false);
  });

  it("rejects missing file object", () => {
    expect(OpenAIFileEntrypointInputSchema.safeParse({}).success).toBe(false);
  });
});
