import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiRequest } = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest,
}));

import { detailToJob, retryFailedChunk } from "@/lib/api/translationApi";
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
