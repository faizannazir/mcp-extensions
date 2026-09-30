import { describe, expect, it } from "vitest";
import { OpenAIDeepLinkHostStateSchema } from "./deep-link.js";

describe("OpenAIDeepLinkHostStateSchema", () => {
  it("accepts a valid deep link state", () => {
    const state = { url: "/parts/hex-bolt" };
    expect(OpenAIDeepLinkHostStateSchema.safeParse(state).success).toBe(true);
  });

  it("rejects missing url", () => {
    expect(OpenAIDeepLinkHostStateSchema.safeParse({}).success).toBe(false);
  });

  it("rejects non-string url", () => {
    expect(OpenAIDeepLinkHostStateSchema.safeParse({ url: 123 }).success).toBe(false);
  });
});
