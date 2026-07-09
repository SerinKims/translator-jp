import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppHeader } from "@/components/layout/AppHeader";

describe("AppHeader health badge", () => {
  it("shows degraded health and opens health details", async () => {
    const user = userEvent.setup();
    const onOpenHealthDetails = vi.fn();
    render(
      <AppHeader
        activeSection="translate"
        currentPageIndex={0}
        healthState="degraded"
        inputMode="text"
        onOpenHealthDetails={onOpenHealthDetails}
        pageCount={0}
        progress={0}
        statusLabel="대기 중"
      />,
    );

    await user.click(screen.getByRole("button", { name: "시스템 점검 필요" }));
    expect(onOpenHealthDetails).toHaveBeenCalledOnce();
  });
});
