import { delay, readStorage, writeStorage } from "@/lib/api/storage";
import type {
  PageTranslateRequest,
  SourceLanguage,
  TranslationApiResult,
  TranslationJob,
  TranslationPage,
  TranslationRequest,
  TranslationResponse,
  TranslationStatus,
  UrlTranslationRequest,
} from "@/types/translation";

export const TRANSLATION_JOBS_STORAGE_KEY = "translator-next-mock-jobs-v1";

const demoUrlSource = `第一ページです。
少年は夕焼けの空を見上げた。
風が静かに頬を撫でていく。

[newpage]

第二ページです。
彼は小さく息を吐いて、もう一度だけ前を見た。

[newpage]

第三ページです。
遠くで鐘の音が鳴り、物語は静かに動き始めた。`;

export async function translateText(request: TranslationRequest): Promise<TranslationApiResult> {
  await delay();
  const pages = createPages(request.text);
  const job = createJob({
    title: createTextTitle(pages),
    inputMode: "text",
    sourceType: "pasted_text",
    sourceLang: request.source_lang,
    model: request.options.model,
    promptVersion: request.options.prompt_version,
    pages,
    options: request,
  });

  const translatedJob = applyScope(job, request.translate_scope, request.page_index);
  persistJob(translatedJob);
  return toApiResult(translatedJob, request.page_index);
}

export async function translateUrl(request: UrlTranslationRequest): Promise<TranslationApiResult> {
  await delay();
  const pages = createPages(demoUrlSource);
  const job = createJob({
    title: request.url || "URL 번역",
    inputMode: "url",
    sourceType: "url",
    sourceUrl: request.url,
    sourceLang: request.source_lang,
    model: request.options.model,
    promptVersion: request.options.prompt_version,
    pages,
    options: request,
  });

  const translatedJob = applyScope(job, request.translate_scope, request.page_index);
  persistJob(translatedJob);
  return toApiResult(translatedJob, request.page_index);
}

export async function translatePage(jobId: number, pageIndex: number, request: PageTranslateRequest): Promise<TranslationApiResult> {
  await delay();
  const job = getStoredJobs().find((item) => item.jobId === jobId);
  if (!job) {
    throw new Error("번역 작업을 찾을 수 없습니다.");
  }

  const nextJob: TranslationJob = {
    ...job,
    sourceLang: request.source_lang,
    targetLang: request.target_lang,
    model: request.options.model,
    promptVersion: request.options.prompt_version,
    options: {
      model: request.options.model,
      promptVersion: request.options.prompt_version,
      useGlossary: request.use_glossary,
      useCache: request.use_cache,
      preserveNames: request.preserve_names,
      temperature: request.options.temperature,
      topP: request.options.top_p,
      contextWindow: request.options.context_window,
      maxTokens: request.options.max_tokens,
    },
  };

  const translatedJob = translateOnePage(nextJob, pageIndex, "completed");
  persistJob(translatedJob);
  return toApiResult(translatedJob, pageIndex);
}

export async function translateAll(request: TranslationRequest | UrlTranslationRequest): Promise<TranslationApiResult> {
  const result = "url" in request ? await translateUrl({ ...request, translate_scope: "all_pages" }) : await translateText({ ...request, translate_scope: "all_pages" });
  return result;
}

export function getTranslationJob(jobId: number) {
  return getStoredJobs().find((item) => item.jobId === jobId) ?? null;
}

export function getStoredJobs() {
  return readStorage<TranslationJob[]>(TRANSLATION_JOBS_STORAGE_KEY, []);
}

export function saveStoredJobs(jobs: TranslationJob[]) {
  writeStorage(TRANSLATION_JOBS_STORAGE_KEY, jobs);
}

function persistJob(job: TranslationJob) {
  const jobs = getStoredJobs();
  const index = jobs.findIndex((item) => item.jobId === job.jobId);
  const nextJobs = index >= 0 ? jobs.map((item) => (item.jobId === job.jobId ? job : item)) : [job, ...jobs];
  saveStoredJobs(nextJobs.slice(0, 50));
}

function createPages(text: string): TranslationPage[] {
  const pages = text
    .split(/\n?\[newpage\]\n?/i)
    .map((page) => page.trim())
    .filter(Boolean);

  return (pages.length > 0 ? pages : [text.trim() || ""]).map((page, index) => ({
    index,
    sourceText: page,
    translatedText: "",
    status: "pending",
  }));
}

function createJob(input: {
  title: string;
  inputMode: "url" | "text";
  sourceType: "url" | "pasted_text";
  sourceUrl?: string;
  sourceLang: SourceLanguage;
  model: string;
  promptVersion: string;
  pages: TranslationPage[];
  options: TranslationRequest | UrlTranslationRequest;
}): TranslationJob {
  const now = new Date().toISOString();
  const jobId = Date.now();
  return {
    id: `job-${jobId}`,
    jobId,
    title: input.title,
    inputMode: input.inputMode,
    sourceType: input.sourceType,
    sourceUrl: input.sourceUrl,
    sourceLang: input.sourceLang,
    targetLang: "ko",
    model: input.model,
    promptVersion: input.promptVersion,
    options: {
      model: input.model,
      promptVersion: input.promptVersion,
      useGlossary: input.options.use_glossary,
      useCache: input.options.use_cache,
      preserveNames: input.options.preserve_names,
      temperature: input.options.options.temperature,
      topP: input.options.options.top_p,
      contextWindow: input.options.options.context_window,
      maxTokens: input.options.options.max_tokens,
    },
    pages: input.pages,
    currentPageIndex: 0,
    status: "ready",
    createdAt: now,
    updatedAt: now,
  };
}

function applyScope(job: TranslationJob, scope: TranslationRequest["translate_scope"], pageIndex: number) {
  if (scope === "all_pages") {
    return job.pages.reduce((currentJob, page) => translateOnePage(currentJob, page.index, "completed"), job);
  }

  const targetIndex = scope === "first_page" ? 0 : pageIndex;
  return translateOnePage(job, targetIndex, "completed");
}

function translateOnePage(job: TranslationJob, pageIndex: number, status: TranslationStatus): TranslationJob {
  const pages = job.pages.map((page) =>
    page.index === pageIndex
      ? {
          ...page,
          translatedText: formatMockTranslation(page.sourceText, job),
          status: "completed" as const,
        }
      : page,
  );

  return {
    ...job,
    pages,
    currentPageIndex: Math.min(Math.max(pageIndex, 0), Math.max(pages.length - 1, 0)),
    status,
    updatedAt: new Date().toISOString(),
  };
}

function toApiResult(job: TranslationJob, pageIndex: number): TranslationApiResult {
  const currentPageIndex = Math.min(Math.max(pageIndex, 0), Math.max(job.pages.length - 1, 0));
  const page = job.pages[currentPageIndex];
  const response: TranslationResponse = {
    job_id: job.jobId,
    source_type: job.sourceType,
    source_lang: job.sourceLang,
    target_lang: job.targetLang,
    current_page_index: currentPageIndex,
    total_pages: job.pages.length,
    has_next_page: currentPageIndex < job.pages.length - 1,
    translated_text: page?.translatedText ?? "",
    model: job.model,
    prompt_version: job.promptVersion,
    style: "webnovel",
    elapsed_ms: 240 + job.pages.filter((item) => item.status === "completed").length * 90,
    cache_hit: job.options.useCache && page?.status === "completed",
    chunks: [
      {
        index: currentPageIndex,
        source_lang: job.sourceLang,
        target_lang: job.targetLang,
        status: page?.status ?? "pending",
      },
    ],
  };

  return { response, job };
}

function formatMockTranslation(source: string, job: TranslationJob) {
  const translated = mockTranslate(source);
  return `[mock 번역 결과 / ${languageLabel(job.sourceLang)} -> 한국어]

${translated}

---
모델: ${job.model}
Prompt: ${job.promptVersion}
용어집 사용: ${job.options.useGlossary ? "ON" : "OFF"}
Cache 사용: ${job.options.useCache ? "ON" : "OFF"}
고유명사 보존: ${job.options.preserveNames ? "ON" : "OFF"}
Temperature: ${job.options.temperature}`;
}

function mockTranslate(source: string) {
  return source
    .replaceAll("第一ページです。", "첫 번째 페이지입니다.")
    .replaceAll("第二ページです。", "두 번째 페이지입니다.")
    .replaceAll("第三ページです。", "세 번째 페이지입니다.")
    .replaceAll("少年は夕焼けの空を見上げた。", "소년은 노을빛 하늘을 올려다보았다.")
    .replaceAll("風が静かに頬を撫でていく。", "바람이 조용히 뺨을 스치고 지나갔다.")
    .replaceAll("彼は小さく息を吐いて、もう一度だけ前を見た。", "그는 작게 숨을 내쉬고, 다시 한 번만 앞을 바라보았다.")
    .replaceAll("遠くで鐘の音が鳴り、物語は静かに動き始めた。", "멀리서 종소리가 울리고, 이야기는 조용히 움직이기 시작했다.");
}

function createTextTitle(pages: TranslationPage[]) {
  const firstLine = pages[0]?.sourceText.split("\n")[0]?.trim();
  return firstLine ? `텍스트 번역 - ${firstLine.slice(0, 30)}` : "텍스트 번역";
}

function languageLabel(language: SourceLanguage) {
  const labels: Record<SourceLanguage, string> = {
    ja: "일본어",
    "zh-TW": "중국어 번체",
    "zh-CN": "중국어 간체",
    en: "영어",
  };
  return labels[language];
}
