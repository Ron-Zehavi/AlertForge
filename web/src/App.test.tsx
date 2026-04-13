import { describe, it, expect } from "vitest";

describe("App", () => {
  it("module loads", async () => {
    const mod = await import("./App");
    expect(mod.default).toBeDefined();
  });
});
