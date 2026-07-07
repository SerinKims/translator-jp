import { apiRequest } from "@/lib/api/client";
import type { PixivFetchResponse } from "@/types/source";
import type {
  InputMode,
  PageStatus,
  PageTranslateRequest,
  SourceLanguage,
  TargetLanguage,
  TranslationApiResult,
  TranslationJob,
  TranslationOptions,
  TranslationPage,
  TranslationRequest,
  TranslationResponse,
  TranslationStatus,
  UrlTranslationRequest,
} from "@/types/translation";
import type {
  TranslationDetailApiResponse,
  TranslationHistoryApiItem,
  TranslationPageHistoryApiItem,
} from "@/types/history";

const NEW_PAGE_PATTERN = /\r?\n?\[newpage\]\r?\n?/i;

type RequestOptionSource = Pick<
  TranslationRequest,
  "client_options" | "style" | "honorific_policy" | "think" | "use_glossary" | "use_cache" | "preserve_names" | "options"
>;

export async function translateText(request: TranslationRequest): Promise<TranslationApiResult> {
  const response = await apiRequest<TranslationResponse>("/api/translate", {
    method: "POST",
    body: JSON.stringify(toTranslationPayload(request)),
  });
  return responseToResult(response, {
    inputMode: "text",
    sourceText: request.text,
    options: requestToOptions(request, response),
  });
}

export async function translateUrl(request: UrlTranslationRequest): Promise<TranslationApiResult> {
  const { fetchAndTranslatePixiv } = await import("@/lib/api/sourceApi");
  const response = await fetchAndTranslatePixiv(request);
  const result = await responseToResult(
    {
      job_id: response.job_id,
      source_type: "url",
      source_lang: request.source_lang,
      target_lang: request.target_lang,
      current_page_index: response.current_page_index,
      total_pages: response.total_pages,
      has_next_page: response.has_next_page,
      translated_text: response.translated_text,
      model: response.model,
      prompt_version: response.prompt_version,
      style: request.style,
      elapsed_ms: response.elapsed_ms,
      cache_hit: false,
      chunks: response.chunks,
    },
    {
      inputMode: "url",
      sourceText: "",
      options: requestToOptions(request, {
        model: response.model,
        prompt_version: response.prompt_version,
      }),
      source: {
        source_site: response.source_site,
        source_url: response.source_url,
        source_work_id: response.source_work_id,
        title: response.title,
        author: response.author,
        text: "",
        char_count: 0,
        job_id: response.job_id,
      },
    },
  );
  return result;
}

export async function translatePage(
  jobId: number,
  pageIndex: number,
  request: PageTranslateRequest,
): Promise<TranslationApiResult> {
  const response = await apiRequest<TranslationResponse>(`/api/translations/${jobId}/pages/${pageIndex}/translate`, {
    method: "POST",
    body: JSON.stringify(toPagePayload(request)),
  });
  return responseToResult(response, {
    inputMode: "url",
    sourceText: "",
    options: requestToOptions(request, response),
  });
}

export async function translateAll(request: TranslationRequest | UrlTranslationRequest): Promise<TranslationApiResult> {
  if ("url" in request) {
    return translateUrl({ ...request, translate_scope: "all_pages" });
  }
  return translateText({ ...request, translate_scope: "all_pages" });
}

export async function retryFailedChunk(jobId: number, chunkIndex: number): Promise<TranslationApiResult> {
  const response = await apiRequest<TranslationResponse>(`/api/translations/${jobId}/chunks/${chunkIndex}/retry`, {
    method: "POST",
  });
  return responseToResult(response, {
    inputMode: "text",
    sourceText: "",
    options: responseToOptions(response),
  });
}

export async function getTranslationJob(jobId: number, fallback?: Partial<TranslationJob>): Promise<TranslationJob> {
  const detail = await apiRequest<TranslationDetailApiResponse>(`/api/translations/${jobId}`);
  return detailToJob(detail, fallback);
}

export function createPendingJobFromText(input: {
  text: string;
  sourceLang: SourceLanguage;
  options: TranslationOptions;
}): TranslationJob {
  const now = new Date().toISOString();
  const pages = splitPages(input.text).map((sourceText, index) => ({
    index,
    sourceText,
    translatedText: "",
    status: "pending" as const,
  }));

  return {
    id: `local-text-${now}`,
    jobId: 0,
    title: createTextTitle(pages),
    inputMode: "text",
    sourceType: "pasted_text",
    sourceLang: input.sourceLang,
    targetLang: "ko",
    model: input.options.model,
    promptVersion: input.options.promptVersion ?? "auto",
    options: input.options,
    pages,
    currentPageIndex: 0,
    status: "ready",
    sourcePreview: pages[0]?.sourceText.slice(0, 160) ?? "",
    translatedPreview: "",
    createdAt: now,
    updatedAt: now,
  };
}

export function createPendingJobFromSource(input: {
  source: PixivFetchResponse;
  sourceLang: SourceLanguage;
  options: TranslationOptions;
}): TranslationJob {
  const now = new Date().toISOString();
  const pages = splitPages(input.source.text).map((sourceText, index) => ({
    index,
    sourceText,
    translatedText: "",
    status: "fetched" as const,
  }));

  return {
    id: `job-${input.source.job_id}`,
    jobId: input.source.job_id,
    title: input.source.title,
    inputMode: "url",
    sourceType: "url",
    sourceUrl: input.source.source_url,
    sourceSite: input.source.source_site,
    sourceAuthor: input.source.author,
    sourceWorkId: input.source.source_work_id,
    sourceLang: input.sourceLang,
    targetLang: "ko",
    model: input.options.model,
    promptVersion: input.options.promptVersion ?? "auto",
    options: input.options,
    pages,
    currentPageIndex: 0,
    status: "fetched",
    sourcePreview: pages[0]?.sourceText.slice(0, 160) ?? "",
    translatedPreview: "",
    createdAt: now,
    updatedAt: now,
  };
}

export function splitPages(text: string): string[] {
  const pages = text
    .split(NEW_PAGE_PATTERN)
    .map((page) => page.trim())
    .filter(Boolean);
  return pages.length > 0 ? pages : [text.trim()];
}

async function responseToResult(
  response: TranslationResponse,
  fallback: {
    inputMode: InputMode;
    sourceText: string;
    options: TranslationOptions;
    source?: PixivFetchResponse;
  },
): Promise<TranslationApiResult> {
  try {
    const job = await getTranslationJob(response.job_id, {
      inputMode: fallback.inputMode,
      options: fallback.options,
      sourceLang: normalizeSourceLanguage(response.source_lang),
      targetLang: normalizeTargetLanguage(response.target_lang),
    });
    return { response, job: mergeResponseIntoJob(job, response) };
  } catch {
    return {
      response,
      job: fallback.source
        ? mergeResponseIntoJob(createPendingJobFromSource({
            source: fallback.source,
            sourceLang: normalizeSourceLanguage(response.source_lang),
            options: fallback.options,
          }), response)
        : fallbackResponseToJob(response, fallback),
    };
  }
}

export function detailToJob(detail: TranslationDetailApiResponse, fallback?: Partial<TranslationJob>): TranslationJob {
  const options = parseOptions(detail, fallback?.options);
  const pages = detail.pages.length > 0
    ? detail.pages
        .slice()
        .sort((a, b) => a.page_index - b.page_index)
        .map(apiPageToPage)
    : splitPages(detail.original_text).map((sourceText, index) => ({
        index,
        sourceText,
        translatedText: "",
        status: "pending" as const,
      }));

  const inputMode: InputMode = detail.source_url ? "url" : fallback?.inputMode ?? "text";
  const translatedCount = pages.filter((page) => page.status === "completed").length;

  return {
    id: `job-${detail.job_id}`,
    jobId: detail.job_id,
    title: detail.source_title || createTextTitle(pages),
    inputMode,
    sourceType: inputMode === "url" ? "url" : "pasted_text",
    sourceUrl: detail.source_url ?? undefined,
    sourceSite: detail.source_site,
    sourceAuthor: detail.source_author,
    sourceWorkId: detail.source_work_id,
    sourceFetchedAt: detail.source_fetched_at,
    sourceLang: normalizeSourceLanguage(detail.source_lang),
    targetLang: normalizeTargetLanguage(detail.target_lang),
    model: detail.model_name,
    promptVersion: detail.prompt_version,
    options,
    pages,
    currentPageIndex: clampIndex(fallback?.currentPageIndex ?? 0, pages.length),
    status: normalizeTranslationStatus(detail.status, translatedCount, pages.length),
    sourcePreview: detail.source_preview,
    translatedPreview: detail.translated_preview ?? "",
    errorMessage: detail.error_message,
    createdAt: detail.created_at,
    updatedAt: detail.updated_at,
  };
}

export function historyItemToJob(item: TranslationHistoryApiItem, fallback?: Partial<TranslationJob>): TranslationJob {
  const nowPages = fallback?.pages ?? [
    {
      index: 0,
      sourceText: item.source_preview,
      translatedText: item.translated_preview ?? "",
      status: item.completed_chunks > 0 ? "completed" as const : "pending" as const,
    },
  ];
  return {
    id: `job-${item.job_id}`,
    jobId: item.job_id,
    title: item.source_title || item.source_preview.slice(0, 30) || `번역 작업 ${item.job_id}`,
    inputMode: item.source_url ? "url" : "text",
    sourceType: item.source_url ? "url" : "pasted_text",
    sourceUrl: item.source_url ?? undefined,
    sourceSite: item.source_site,
    sourceAuthor: item.source_author,
    sourceWorkId: item.source_work_id,
    sourceFetchedAt: item.source_fetched_at,
    sourceLang: normalizeSourceLanguage(item.source_lang),
    targetLang: normalizeTargetLanguage(item.target_lang),
    model: item.model_name,
    promptVersion: item.prompt_version,
    options: parseOptions(item, fallback?.options),
    pages: nowPages,
    currentPageIndex: 0,
    status: normalizeTranslationStatus(item.status, item.completed_chunks, item.total_chunks),
    sourcePreview: item.source_preview,
    translatedPreview: item.translated_preview ?? "",
    errorMessage: item.error_message,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

function fallbackResponseToJob(
  response: TranslationResponse,
  fallback: {
    inputMode: InputMode;
    sourceText: string;
    options: TranslationOptions;
  },
): TranslationJob {
  const sourcePages = splitPages(fallback.sourceText);
  const pages: TranslationPage[] = Array.from({ length: Math.max(response.total_pages, sourcePages.length, 1) }, (_, index) => ({
    index,
    sourceText: sourcePages[index] ?? "",
    translatedText: index === response.current_page_index ? response.translated_text : "",
    status: index === response.current_page_index && response.translated_text ? "completed" : "pending",
  }));
  return {
    id: `job-${response.job_id}`,
    jobId: response.job_id,
    title: createTextTitle(pages),
    inputMode: fallback.inputMode,
    sourceType: fallback.inputMode === "url" ? "url" : "pasted_text",
    sourceLang: normalizeSourceLanguage(response.source_lang),
    targetLang: normalizeTargetLanguage(response.target_lang),
    model: response.model,
    promptVersion: response.prompt_version,
    options: { ...fallback.options, promptVersion: response.prompt_version },
    pages,
    currentPageIndex: response.current_page_index,
    status: response.translated_text ? "completed" : "ready",
    sourcePreview: pages[0]?.sourceText.slice(0, 160) ?? "",
    translatedPreview: response.translated_text.slice(0, 160),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

function mergeResponseIntoJob(job: TranslationJob, response: TranslationResponse): TranslationJob {
  const pages = job.pages.map((page) =>
    page.index === response.current_page_index
      ? {
          ...page,
          translatedText: response.translated_text || page.translatedText,
          status: response.translated_text ? "completed" as const : page.status,
        }
      : page,
  );
  return {
    ...job,
    model: response.model,
    promptVersion: response.prompt_version,
    options: { ...job.options, promptVersion: response.prompt_version },
    pages,
    currentPageIndex: clampIndex(response.current_page_index, pages.length),
    status: pages.every((page) => page.status === "completed") ? "completed" : "loaded",
    translatedPreview: pages.find((page) => page.translatedText)?.translatedText.slice(0, 160) ?? job.translatedPreview,
    updatedAt: new Date().toISOString(),
  };
}

function apiPageToPage(page: TranslationPageHistoryApiItem): TranslationPage {
  return {
    id: page.id,
    index: page.page_index,
    title: page.page_title,
    sourceText: page.source_text,
    translatedText: page.translated_text ?? "",
    status: normalizePageStatus(page.status),
    totalChunks: page.total_chunks,
    completedChunks: page.completed_chunks,
    failedChunks: page.failed_chunks,
    errorMessage: page.error_message,
  };
}

function requestToOptions(
  request: RequestOptionSource,
  response: Pick<TranslationResponse, "model" | "prompt_version">,
): TranslationOptions {
  const clientOptions = request.client_options;
  return {
    model: clientOptions?.model ?? response.model,
    promptVersion: response.prompt_version,
    useGlossary: request.use_glossary,
    useCache: request.use_cache,
    preserveNames: request.preserve_names,
    style: request.style,
    honorificPolicy: request.honorific_policy,
    think: request.think,
    temperature: request.options.temperature,
    topP: request.options.top_p,
    contextWindow: request.options.num_ctx,
    maxTokens: request.options.num_predict,
  };
}

function toTranslationPayload(request: TranslationRequest): Omit<TranslationRequest, "client_options"> {
  const payload = { ...request };
  delete payload.client_options;
  return payload;
}

function toPagePayload(request: PageTranslateRequest): Omit<PageTranslateRequest, "client_options"> {
  const payload = { ...request };
  delete payload.client_options;
  return payload;
}

function responseToOptions(response: Pick<TranslationResponse, "model" | "prompt_version">): TranslationOptions {
  return {
    model: response.model,
    promptVersion: response.prompt_version,
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
  };
}

function parseOptions(
  item: Pick<
    TranslationHistoryApiItem,
    "ollama_options_json" | "ollama_think" | "model_name" | "prompt_version" | "style" | "honorific_policy" | "preserve_names"
  >,
  fallback?: TranslationOptions,
): TranslationOptions {
  const parsed = parseOllamaOptions(item.ollama_options_json);
  return {
    model: item.model_name || fallback?.model || "gemma4:26b-a4b-it-q4_K_M",
    promptVersion: item.prompt_version || fallback?.promptVersion || "translate_ja_ko_v1",
    style: normalizeStyle(item.style || fallback?.style),
    honorificPolicy: normalizeHonorificPolicy(item.honorific_policy || fallback?.honorificPolicy),
    think: parseThink(item.ollama_think, fallback?.think),
    useGlossary: fallback?.useGlossary ?? true,
    useCache: fallback?.useCache ?? true,
    preserveNames: item.preserve_names,
    temperature: numberOption(parsed.temperature, fallback?.temperature ?? 0.3),
    topP: numberOption(parsed.top_p, fallback?.topP ?? 0.9),
    contextWindow: numberOption(parsed.num_ctx, fallback?.contextWindow ?? 8192),
    maxTokens: numberOption(parsed.num_predict, fallback?.maxTokens ?? 4096),
  };
}

function parseThink(value: string | null, fallback: string | boolean = false): string | boolean {
  if (!value) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(value) as unknown;
    return typeof parsed === "string" || typeof parsed === "boolean" ? parsed : fallback;
  } catch {
    return value;
  }
}

function normalizeStyle(value: string | undefined): TranslationOptions["style"] {
  if (value === "lightnovel" || value === "literal" || value === "natural") {
    return value;
  }
  return "webnovel";
}

function normalizeHonorificPolicy(value: string | undefined): TranslationOptions["honorificPolicy"] {
  if (value === "naturalize" || value === "omit") {
    return value;
  }
  return "preserve";
}

function parseOllamaOptions(value: string | null): Record<string, unknown> {
  if (!value) {
    return {};
  }
  try {
    const parsed = JSON.parse(value) as unknown;
    return typeof parsed === "object" && parsed !== null ? parsed as Record<string, unknown> : {};
  } catch {
    return {};
  }
}

function numberOption(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function normalizeSourceLanguage(value: string): SourceLanguage {
  if (value === "auto" || value === "ja" || value === "zh-TW" || value === "zh-CN" || value === "en") {
    return value;
  }
  return "ja";
}

function normalizeTargetLanguage(value: string): TargetLanguage {
  return value === "ko" ? "ko" : "ko";
}

function normalizePageStatus(value: string): PageStatus {
  if (
    value === "pending" ||
    value === "pending_translation" ||
    value === "in_progress" ||
    value === "fetched" ||
    value === "completed" ||
    value === "failed"
  ) {
    return value;
  }
  return value === "translated" ? "completed" : "pending";
}

function normalizeTranslationStatus(value: string, completed: number, total: number): TranslationStatus {
  if (value === "failed") {
    return "failed";
  }
  if (value === "fetched" || value === "pending_translation" || value === "translating" || value === "loaded") {
    return value;
  }
  if (completed > 0 && total > 0 && completed >= total) {
    return "completed";
  }
  if (completed > 0) {
    return "loaded";
  }
  return "ready";
}

function clampIndex(index: number, pageCount: number): number {
  return Math.min(Math.max(index, 0), Math.max(pageCount - 1, 0));
}

function createTextTitle(pages: TranslationPage[]): string {
  const firstLine = pages[0]?.sourceText.split(/\r?\n/)[0]?.trim();
  return firstLine ? `텍스트 번역 - ${firstLine.slice(0, 30)}` : "텍스트 번역";
}
