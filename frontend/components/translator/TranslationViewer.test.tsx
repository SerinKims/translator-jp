import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TranslationViewer } from "@/components/translator/TranslationViewer";
import type { TranslationJob } from "@/types/translation";

const job: TranslationJob = {
  id: "job-1",
  jobId: 1,
  title: "실패 작업",
  inputMode: "text",
  sourceType: "pasted_text",
  sourceLang: "ja",
  targetLang: "ko",
  model: "gemma4:26b-a4b-it-q4_K_M",
  promptVersion: "translate_ja_ko_v1",
  options: {
    model: "gemma4:26b-a4b-it-q4_K_M",
    style: "webnovel",
    honorificPolicy: "preserve",
    think: false,
    useGlossary: true,
    useCache: true,
    preserveNames: true,
    temperature: 0.3,
    topP: 0.9,
    contextWindow: 8192,
    maxTokens: 4096,
  },
  pages: [
    { id: 10, index: 0, sourceText: "첫 페이지", translatedText: "", status: "failed" },
    { id: 11, index: 1, sourceText: "둘째 페이지", translatedText: "", status: "failed" },
  ],
  chunks: [
    {
      id: 100,
      pageId: 10,
      pageIndex: 0,
      index: 0,
      sourceText: "현재 페이지 실패 원문",
      translatedText: "",
      status: "failed",
      retryCount: 1,
      errorMessage: "model timeout",
    },
    {
      id: 101,
      pageId: 11,
      pageIndex: 1,
      index: 0,
      sourceText: "다른 페이지 실패 원문",
      translatedText: "",
      status: "failed",
      retryCount: 0,
      errorMessage: "other error",
    },
  ],
  currentPageIndex: 0,
  status: "failed",
  createdAt: "2026-07-09T00:00:00",
  updatedAt: "2026-07-09T00:00:00",
};

function renderViewer(onRetryChunk = vi.fn(), retryingChunkKey: string | null = null) {
  render(
    <TranslationViewer
      currentJob={job}
      currentPageIndex={0}
      errorMessage={null}
      isTranslating={false}
      onPageChange={vi.fn()}
      onRetryChunk={onRetryChunk}
      onTranslateAllText={vi.fn()}
      onTranslateAllUrl={vi.fn()}
      onTranslateCurrent={vi.fn()}
      retryingChunkKey={retryingChunkKey}
      setViewerMode={vi.fn()}
      viewerMode="translation"
    />,
  );
}

describe("TranslationViewer failed chunks", () => {
  it("shows only failed chunks from the current page and retries the selected chunk", async () => {
    const user = userEvent.setup();
    const onRetryChunk = vi.fn();
    renderViewer(onRetryChunk);

    expect(screen.getByText("현재 페이지 실패 원문")).toBeInTheDocument();
    expect(screen.queryByText("다른 페이지 실패 원문")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Chunk 1 재시도" }));
    expect(onRetryChunk).toHaveBeenCalledWith(0, 0);
  });

  it("disables the chunk button while that chunk is retrying", () => {
    renderViewer(vi.fn(), "0:0");
    expect(screen.getByRole("button", { name: "Chunk 1 재시도 중" })).toBeDisabled();
  });
});
