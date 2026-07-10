import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CacheManagementCard } from "@/components/settings/CacheManagementCard";

describe("CacheManagementCard", () => {
  it("opens a confirmation dialog and clears the translation cache", async () => {
    const user = userEvent.setup();
    const clearCache = vi.fn();
    render(
      <CacheManagementCard
        clearCache={clearCache}
        error={null}
        isClearing={false}
        isSuccess={false}
      />,
    );

    expect(screen.getByText("캐시 관리")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "캐시 삭제" }));

    const dialog = screen.getByRole("alertdialog");
    expect(within(dialog).getByText("번역 캐시를 삭제할까요?")).toBeInTheDocument();

    await user.click(within(dialog).getByRole("button", { name: "캐시 삭제" }));

    expect(clearCache).toHaveBeenCalledOnce();
  });

  it("disables the clear action while cache deletion is pending", () => {
    render(
      <CacheManagementCard
        clearCache={vi.fn()}
        error={null}
        isClearing
        isSuccess={false}
      />,
    );

    expect(screen.getByRole("button", { name: "캐시 삭제" })).toBeDisabled();
  });

  it("shows a success message after cache deletion", () => {
    render(
      <CacheManagementCard
        clearCache={vi.fn()}
        error={null}
        isClearing={false}
        isSuccess
      />,
    );

    expect(screen.getByText("번역 캐시를 삭제했습니다. 다음 번역부터 새로 생성된 결과가 저장됩니다.")).toBeInTheDocument();
  });

  it("shows a failure message when cache deletion fails", () => {
    render(
      <CacheManagementCard
        clearCache={vi.fn()}
        error={new Error("cache clear failed")}
        isClearing={false}
        isSuccess={false}
      />,
    );

    expect(screen.getByText("cache clear failed")).toBeInTheDocument();
  });
});
