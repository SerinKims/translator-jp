import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { TranslationResult } from "@/components/translation-result"
import type {
  TranslationChunk,
  TranslationDetailResponse,
  TranslationPageHistory,
} from "@/lib/types"

const basePage = {
  id: 1,
  page_title: null,
  source_text: "source",
  translated_text: null,
  total_chunks: 0,
  completed_chunks: 0,
  failed_chunks: 0,
  elapsed_ms: null,
  error_message: null,
  created_at: "2026-07-02T00:00:00",
  updated_at: "2026-07-02T00:00:00",
}

function makePage(
  page_index: number,
  status: string,
  translated_text: string | null,
): TranslationPageHistory {
  return {
    ...basePage,
    id: page_index + 1,
    page_index,
    status,
    source_text: `source ${page_index + 1}`,
    translated_text,
  }
}

function makeDetail(
  pages: TranslationPageHistory[],
): TranslationDetailResponse {
  return {
    job_id: 1,
    source_site: "manual",
    source_url: null,
    source_title: null,
    source_author: null,
    source_work_id: null,
    source_fetched_at: null,
    source_preview: "source",
    translated_preview: "translated",
    source_lang: "ja",
    target_lang: "ko",
    model_name: "gemma4:26b-a4b-it-q4_K_M",
    prompt_version: "translate_ja_ko_v1",
    ollama_think: null,
    ollama_options_json: null,
    style: "webnovel",
    honorific_policy: "preserve",
    preserve_names: true,
    status: "pending_translation",
    total_pages: pages.length,
    total_chunks: 1,
    completed_chunks: 1,
    failed_chunks: 0,
    elapsed_ms: null,
    error_message: null,
    created_at: "2026-07-02T00:00:00",
    updated_at: "2026-07-02T00:00:00",
    original_text: "source 1[newpage]source 2",
    translated_text: "translated 1",
    pages,
    chunks: [],
  }
}

const chunks: TranslationChunk[] = [
  {
    index: 0,
    source_text: "source 1",
    translated_text: "translated 1",
    status: "completed",
  },
]

describe("TranslationResult", () => {
  it("renders previous and next page controls with boundary states", () => {
    const onPageChange = vi.fn()
    render(
      <TranslationResult
        detail={makeDetail([
          makePage(0, "completed", "translated 1"),
          makePage(1, "pending", null),
        ])}
        chunks={chunks}
        currentPageIndex={0}
        viewMode="translation_only"
        onViewModeChange={vi.fn()}
        onPageChange={onPageChange}
        onTranslateCurrentPage={vi.fn()}
        onTranslateAllPages={vi.fn()}
        onCopy={vi.fn()}
      />,
    )

    expect(screen.getByRole("button", { name: /이전 페이지/ })).toBeDisabled()
    fireEvent.click(screen.getByRole("button", { name: /다음 페이지/ }))

    expect(onPageChange).toHaveBeenCalledWith(1)
  })

  it("shows current page translation action for an untranslated page", () => {
    const onTranslateCurrentPage = vi.fn()
    render(
      <TranslationResult
        detail={makeDetail([
          makePage(0, "completed", "translated 1"),
          makePage(1, "pending", null),
        ])}
        chunks={[
          {
            index: 0,
            source_text: "source 2",
            translated_text: null,
            status: "pending",
          },
        ]}
        currentPageIndex={1}
        viewMode="parallel"
        onViewModeChange={vi.fn()}
        onPageChange={vi.fn()}
        onTranslateCurrentPage={onTranslateCurrentPage}
        onTranslateAllPages={vi.fn()}
        onCopy={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: /현재 페이지 번역/ }))

    expect(onTranslateCurrentPage).toHaveBeenCalledTimes(1)
  })
})
