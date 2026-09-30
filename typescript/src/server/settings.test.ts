import { describe, expect, it } from "vitest";
import {
  OpenAISettingsCapabilitySchema,
  OpenAISettingsReadResultSchema,
  OpenAISettingsUpdateArgumentsSchema,
  OpenAISettingsUpdateResultSchema,
} from "./settings.js";

describe("OpenAISettingsCapabilitySchema", () => {
  it("accepts a valid capability", () => {
    const cap = { readTool: "settings.read", updateTool: "settings.update" };
    expect(OpenAISettingsCapabilitySchema.safeParse(cap).success).toBe(true);
  });

  it("rejects blank tool names", () => {
    expect(
      OpenAISettingsCapabilitySchema.safeParse({ readTool: "", updateTool: "s.u" })
        .success,
    ).toBe(false);
  });
});

describe("OpenAISettingsReadResultSchema", () => {
  it("accepts a valid read result", () => {
    const result = {
      schema: {
        type: "object",
        properties: {
          units: { type: "string", title: "Units", enum: ["mm", "in"] },
        },
      },
      values: { units: "mm" },
    };
    expect(OpenAISettingsReadResultSchema.safeParse(result).success).toBe(true);
  });

  it("rejects layout referencing unknown properties", () => {
    const result = {
      schema: { type: "object", properties: {} },
      values: {},
      layout: [
        {
          kind: "group",
          title: "Group",
          items: [{ kind: "property", property: "unknown" }],
        },
      ],
    };
    expect(OpenAISettingsReadResultSchema.safeParse(result).success).toBe(false);
  });

  it("rejects duplicate layout references", () => {
    const result = {
      schema: {
        type: "object",
        properties: { units: { type: "string", title: "Units" } },
      },
      values: { units: "mm" },
      layout: [
        {
          kind: "group",
          title: "Group",
          items: [
            { kind: "property", property: "units" },
            { kind: "property", property: "units" },
          ],
        },
      ],
    };
    expect(OpenAISettingsReadResultSchema.safeParse(result).success).toBe(false);
  });
});

describe("OpenAISettingsUpdateArgumentsSchema", () => {
  it("accepts a non-empty set", () => {
    expect(
      OpenAISettingsUpdateArgumentsSchema.safeParse({ set: { units: "in" } }).success,
    ).toBe(true);
  });

  it("rejects an empty set", () => {
    expect(OpenAISettingsUpdateArgumentsSchema.safeParse({ set: {} }).success).toBe(
      false,
    );
  });
});

describe("OpenAISettingsUpdateResultSchema", () => {
  it("accepts a valid update result", () => {
    expect(
      OpenAISettingsUpdateResultSchema.safeParse({ values: { units: "in" } }).success,
    ).toBe(true);
  });

  it("rejects missing values", () => {
    expect(OpenAISettingsUpdateResultSchema.safeParse({}).success).toBe(false);
  });
});
