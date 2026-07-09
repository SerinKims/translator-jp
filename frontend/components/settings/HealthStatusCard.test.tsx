import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { HealthStatusCard } from "@/components/settings/HealthStatusCard";

describe("HealthStatusCard", () => {
  it("renders component states and supports manual refresh", async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();
    render(
      <HealthStatusCard
        error={null}
        health={{
          status: "ok",
          ollama: "error",
          database: "ok",
          model: "gemma4:26b-a4b-it-q4_K_M",
          message: "Ollama를 사용할 수 없습니다.",
        }}
        isFetching={false}
        onRefresh={onRefresh}
      />,
    );

    expect(screen.getByText("Backend 연결")).toBeInTheDocument();
    expect(screen.getByText("Ollama를 사용할 수 없습니다.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "상태 새로고침" }));
    expect(onRefresh).toHaveBeenCalledOnce();
  });

  it("distinguishes an HTTP connection failure", () => {
    render(
      <HealthStatusCard
        error={new Error("Failed to fetch")}
        health={undefined}
        isFetching={false}
        onRefresh={vi.fn()}
      />,
    );

    expect(screen.getByText("Backend에 연결할 수 없습니다.")).toBeInTheDocument();
  });
});
