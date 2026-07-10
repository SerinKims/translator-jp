import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiRequest } = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest,
}));

import { detailToJob, retryFailedChunk, savePageTranslation } from "@/lib/api/translationApi";
import type { TranslationDetailApiResponse } from "@/types/history";

describe("retryFailedChunk", () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it("uses the page-scoped retry endpoint", async () => {
    apiRequest
      .mockResolvedValueOnce({
        job_id: 7,
        source_type: "pasted_text",
        source_lang: "ja",
        target_lang: "ko",
        current_page_index: 2,
        total_pages: 3,
        has_next_page: false,
        translated_text: "재시도 결과",
        model: "gemma4:26b-a4b-it-q4_K_M",
        prompt_version: "translate_ja_ko_v1",
        style: "webnovel",
        elapsed_ms: 10,
        cache_hit: false,
        chunks: [],
      })
      .mockRejectedValueOnce(new Error("detail unavailable"));

    await retryFailedChunk(7, 2, 1);

    expect(apiRequest).toHaveBeenNthCalledWith(
      1,
      "/api/translations/7/pages/2/chunks/1/retry",
      { method: "POST" },
    );
  });
});

describe("savePageTranslation", () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it("uses the page translation edit endpoint", async () => {
    apiRequest.mockResolvedValueOnce(createDetail({
      translated_text: "수정본",
      pages: [{
        id: 10,
        page_index: 2,
        page_title: null,
        source_text: "원문",
        translated_text: "수정본",
        status: "completed",
        total_chunks: 1,
        completed_chunks: 1,
        failed_chunks: 0,
        elapsed_ms: null,
        error_message: null,
        created_at: "2026-07-10T00:00:00",
        updated_at: "2026-07-10T00:00:00",
      }],
    }));

    const job = await savePageTranslation(7, 2, {
      translated_text: "수정본",
      comment: null,
    });

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/translations/7/pages/2/translation",
      {
        method: "PATCH",
        body: JSON.stringify({ translated_text: "수정본", comment: null }),
      },
    );
    expect(job.currentPageIndex).toBe(0);
    expect(job.pages[0].translatedText).toBe("수정본");
  });
});

describe("detailToJob", () => {
  it("preserves chunk details needed by the retry UI", () => {
    const detail = {
      job_id: 7,
      source_site: "manual",
      source_url: null,
      source_title: null,
      source_author: null,
      source_work_id: null,
      source_fetched_at: null,
      source_preview: "실패 원문",
      translated_preview: null,
      source_lang: "ja",
      target_lang: "ko",
      model_name: "gemma4:26b-a4b-it-q4_K_M",
      prompt_version: "translate_ja_ko_v1",
      ollama_think: null,
      ollama_options_json: null,
      style: "webnovel",
      honorific_policy: "preserve",
      preserve_names: true,
      status: "failed",
      total_pages: 1,
      total_chunks: 1,
      completed_chunks: 0,
      failed_chunks: 1,
      elapsed_ms: null,
      error_message: "model timeout",
      created_at: "2026-07-09T00:00:00",
      updated_at: "2026-07-09T00:00:00",
      original_text: "실패 원문",
      translated_text: null,
      pages: [{
        id: 10,
        page_index: 0,
        page_title: null,
        source_text: "실패 원문",
        translated_text: null,
        status: "failed",
        total_chunks: 1,
        completed_chunks: 0,
        failed_chunks: 1,
        elapsed_ms: null,
        error_message: "model timeout",
        created_at: "2026-07-09T00:00:00",
        updated_at: "2026-07-09T00:00:00",
      }],
      chunks: [{
        id: 100,
        page_id: 10,
        page_index: 0,
        chunk_index: 0,
        source_lang: "ja",
        target_lang: "ko",
        source_text: "실패 원문",
        translated_text: null,
        context_before: null,
        context_after: null,
        status: "failed",
        retry_count: 2,
        prompt_used: null,
        raw_model_response: null,
        elapsed_ms: null,
        error_message: "model timeout",
        created_at: "2026-07-09T00:00:00",
        updated_at: "2026-07-09T00:00:00",
      }],
    } satisfies TranslationDetailApiResponse;

    const job = detailToJob(detail);

    expect(job.chunks).toEqual([
      expect.objectContaining({
        pageIndex: 0,
        index: 0,
        retryCount: 2,
        errorMessage: "model timeout",
      }),
    ]);
  });
});

function createDetail(
  overrides: Partial<TranslationDetailApiResponse> = {},
): TranslationDetailApiResponse {
  return {
    job_id: 7,
    source_site: "manual",
    source_url: null,
    source_title: null,
    source_author: null,
    source_work_id: null,
    source_fetched_at: null,
    source_preview: "원문",
    translated_preview: "수정본",
    source_lang: "ja",
    target_lang: "ko",
    model_name: "gemma4:26b-a4b-it-q4_K_M",
    prompt_version: "translate_ja_ko_v1",
    ollama_think: null,
    ollama_options_json: null,
    style: "webnovel",
    honorific_policy: "preserve",
    preserve_names: true,
    status: "completed",
    total_pages: 1,
    total_chunks: 1,
    completed_chunks: 1,
    failed_chunks: 0,
    elapsed_ms: null,
    error_message: null,
    created_at: "2026-07-10T00:00:00",
    updated_at: "2026-07-10T00:00:00",
    original_text: "원문",
    translated_text: "수정본",
    pages: [{
      id: 10,
      page_index: 0,
      page_title: null,
      source_text: "원문",
      translated_text: "수정본",
      status: "completed",
      total_chunks: 1,
      completed_chunks: 1,
      failed_chunks: 0,
      elapsed_ms: null,
      error_message: null,
      created_at: "2026-07-10T00:00:00",
      updated_at: "2026-07-10T00:00:00",
    }],
    chunks: [],
    ...overrides,
  };
}
