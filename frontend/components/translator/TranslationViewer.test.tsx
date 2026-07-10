import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TranslationViewer } from "@/components/translator/TranslationViewer";
import type { GlossaryCandidateCreateRequest } from "@/types/glossary";
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

afterEach(() => {
  vi.restoreAllMocks();
});

function renderViewer({
  currentJob = job,
  onCreateGlossaryCandidate,
  onRetryChunk = vi.fn(),
  onSavePageTranslation,
  isSavingTranslation = false,
  retryingChunkKey = null,
  setViewerMode = vi.fn(),
  viewerMode = "translation",
}: {
  currentJob?: TranslationJob;
  onCreateGlossaryCandidate?: (request: GlossaryCandidateCreateRequest) => void;
  onRetryChunk?: (pageIndex: number, chunkIndex: number) => void;
  onSavePageTranslation?: (translatedText: string, onSaved?: () => void) => void;
  isSavingTranslation?: boolean;
  retryingChunkKey?: string | null;
  setViewerMode?: (mode: "both" | "translation") => void;
  viewerMode?: "both" | "translation";
} = {}) {
  return render(
    <TranslationViewer
      currentJob={currentJob}
      currentPageIndex={0}
      errorMessage={null}
      isTranslating={false}
      isSavingTranslation={isSavingTranslation}
      onCreateGlossaryCandidate={onCreateGlossaryCandidate}
      onPageChange={vi.fn()}
      onRetryChunk={onRetryChunk}
      onSavePageTranslation={onSavePageTranslation}
      onTranslateAllText={vi.fn()}
      onTranslateAllUrl={vi.fn()}
      onTranslateCurrent={vi.fn()}
      retryingChunkKey={retryingChunkKey}
      setViewerMode={setViewerMode}
      viewerMode={viewerMode}
    />,
  );
}

describe("TranslationViewer failed chunks", () => {
  it("shows only failed chunks from the current page and retries the selected chunk", async () => {
    const user = userEvent.setup();
    const onRetryChunk = vi.fn();
    renderViewer({ onRetryChunk });

    expect(screen.getByText("현재 페이지 실패 원문")).toBeInTheDocument();
    expect(screen.queryByText("다른 페이지 실패 원문")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Chunk 1 재시도" }));
    expect(onRetryChunk).toHaveBeenCalledWith(0, 0);
  });

  it("disables the chunk button while that chunk is retrying", () => {
    renderViewer({ retryingChunkKey: "0:0" });
    expect(screen.getByRole("button", { name: "Chunk 1 재시도 중" })).toBeDisabled();
  });
});

describe("TranslationViewer glossary candidate selection", () => {
  it("creates a candidate from selected translated and source terms", async () => {
    const user = userEvent.setup();
    const onCreateGlossaryCandidate = vi.fn();
    const setViewerMode = vi.fn();
    const completedJob = createCompletedJob();
    renderViewer({
      currentJob: completedJob,
      onCreateGlossaryCandidate,
      setViewerMode,
      viewerMode: "both",
    });

    await user.click(screen.getByRole("button", { name: "용어 후보 만들기" }));
    expect(setViewerMode).toHaveBeenCalledWith("both");

    mockSelection("왕도");
    fireEvent.mouseUp(screen.getByText("왕도가 하늘을 올려다보았다."));
    expect(screen.getByText("번역어: 왕도")).toBeInTheDocument();

    mockSelection("王都");
    fireEvent.mouseUp(screen.getByText("王都の空を見上げた。"));
    expect(screen.getByText("원어: 王都")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "후보 등록 확인" }));
    expect(screen.getByText("王都 → 왕도")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "후보 등록" }));
    expect(onCreateGlossaryCandidate).toHaveBeenCalledWith({
      source_lang: "ja",
      target_lang: "ko",
      source_term: "王都",
      suggested_target_term: "왕도",
      source_text: "王都の空を見上げた。",
      model_translation: "왕도가 하늘을 올려다보았다.",
      user_corrected_translation: "왕도가 하늘을 올려다보았다.",
    });
  });

  it("keeps the candidate confirmation disabled until both terms are selected", async () => {
    const user = userEvent.setup();
    renderViewer({
      currentJob: createCompletedJob(),
      onCreateGlossaryCandidate: vi.fn(),
      viewerMode: "both",
    });

    await user.click(screen.getByRole("button", { name: "용어 후보 만들기" }));
    expect(screen.getByRole("button", { name: "후보 등록 확인" })).toBeDisabled();

    mockSelection("왕도");
    fireEvent.mouseUp(screen.getByText("왕도가 하늘을 올려다보았다."));
    expect(screen.getByRole("button", { name: "후보 등록 확인" })).toBeDisabled();
  });
});

describe("TranslationViewer translation editing", () => {
  it("edits and saves the current page translation", async () => {
    const user = userEvent.setup();
    const onSavePageTranslation = vi.fn();
    renderViewer({
      currentJob: createCompletedJob(),
      onSavePageTranslation,
    });

    await user.click(screen.getByRole("button", { name: "수정" }));
    const textarea = screen.getByLabelText("번역문 수정");
    expect(textarea).toHaveValue("왕도가 하늘을 올려다보았다.");

    await user.clear(textarea);
    await user.type(textarea, "왕도는 하늘을 올려다보았다.");
    await user.click(screen.getByRole("button", { name: "저장" }));

    expect(onSavePageTranslation).toHaveBeenCalledWith(
      "왕도는 하늘을 올려다보았다.",
      expect.any(Function),
    );
  });

  it("cancels translation edits and restores the saved text", async () => {
    const user = userEvent.setup();
    const onSavePageTranslation = vi.fn();
    renderViewer({
      currentJob: createCompletedJob(),
      onSavePageTranslation,
    });

    await user.click(screen.getByRole("button", { name: "수정" }));
    const textarea = screen.getByLabelText("번역문 수정");
    await user.clear(textarea);
    await user.type(textarea, "임시 수정");
    await user.click(screen.getByRole("button", { name: "취소" }));

    expect(screen.queryByLabelText("번역문 수정")).not.toBeInTheDocument();
    expect(screen.getByText("왕도가 하늘을 올려다보았다.")).toBeInTheDocument();
    expect(onSavePageTranslation).not.toHaveBeenCalled();
  });

  it("disables edit controls while the save request is pending", async () => {
    const user = userEvent.setup();
    const view = renderViewer({
      currentJob: createCompletedJob(),
      onSavePageTranslation: vi.fn(),
    });

    await user.click(screen.getByRole("button", { name: "수정" }));
    view.rerender(
      <TranslationViewer
        currentJob={createCompletedJob()}
        currentPageIndex={0}
        errorMessage={null}
        isTranslating={false}
        isSavingTranslation
        onPageChange={vi.fn()}
        onRetryChunk={vi.fn()}
        onSavePageTranslation={vi.fn()}
        onTranslateAllText={vi.fn()}
        onTranslateAllUrl={vi.fn()}
        onTranslateCurrent={vi.fn()}
        retryingChunkKey={null}
        setViewerMode={vi.fn()}
        viewerMode="translation"
      />,
    );

    expect(screen.getByRole("button", { name: "저장 중" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "취소" })).toBeDisabled();
    expect(screen.getByLabelText("번역문 수정")).toBeDisabled();
  });
});

function createCompletedJob(): TranslationJob {
  return {
    ...job,
    status: "completed",
    pages: [
      {
        id: 20,
        index: 0,
        sourceText: "王都の空を見上げた。",
        translatedText: "왕도가 하늘을 올려다보았다.",
        status: "completed",
      },
    ],
    chunks: [],
  };
}

function mockSelection(text: string) {
  vi.spyOn(window, "getSelection").mockReturnValue({
    toString: () => text,
  } as Selection);
}
