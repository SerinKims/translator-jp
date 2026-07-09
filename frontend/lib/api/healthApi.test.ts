import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiRequest } = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest,
}));

import { getHealth } from "@/lib/api/healthApi";

describe("getHealth", () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it("requests the backend health endpoint", async () => {
    const response = {
      status: "ok",
      ollama: "ok",
      database: "ok",
      model: "gemma4:26b-a4b-it-q4_K_M",
    };
    apiRequest.mockResolvedValue(response);

    await expect(getHealth()).resolves.toEqual(response);
    expect(apiRequest).toHaveBeenCalledWith("/api/health");
  });
});
