export type SourceLanguage = "ja" | "zh-TW" | "zh-CN" | "en";
export type TargetLanguage = "ko";
export type TranslateScope = "first_page" | "current_page" | "all_pages";
export type InputMode = "url" | "text";
export type ViewerMode = "both" | "translation";
export type PageStatus = "pending" | "completed" | "failed";
export type TranslationStatus = "idle" | "ready" | "translating" | "completed" | "failed" | "loaded";

export interface ModelSettings {
  defaultModel: string;
  promptVersion: string;
  temperature: number;
  topP: number;
  contextWindow: number;
  maxTokens: number;
}

export interface TranslationOptions {
  model: string;
  promptVersion: string;
  useGlossary: boolean;
  useCache: boolean;
  preserveNames: boolean;
  temperature: number;
  topP: number;
  contextWindow: number;
  maxTokens: number;
}

export interface TranslationRequest {
  text: string;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  translate_scope: TranslateScope;
  page_index: number;
  style: "webnovel";
  honorific_policy: "preserve";
  preserve_names: boolean;
  use_glossary: boolean;
  use_cache: boolean;
  stream: false;
  think: false | "low";
  options: {
    model: string;
    prompt_version: string;
    temperature: number;
    top_p: number;
    context_window: number;
    max_tokens: number;
  };
}

export interface UrlTranslationRequest extends Omit<TranslationRequest, "text"> {
  url: string;
  view_mode: ViewerMode;
}

export interface PageTranslateRequest extends Omit<TranslationRequest, "text" | "translate_scope" | "page_index"> {
  force: boolean;
}

export interface TranslationChunkResponse {
  index: number;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  status: PageStatus;
}

export interface TranslationResponse {
  job_id: number;
  source_type: "pasted_text" | "url";
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  current_page_index: number;
  total_pages: number;
  has_next_page: boolean;
  translated_text: string;
  model: string;
  prompt_version: string;
  style: "webnovel";
  elapsed_ms: number;
  cache_hit: boolean;
  chunks: TranslationChunkResponse[];
}

export interface TranslationPage {
  index: number;
  sourceText: string;
  translatedText: string;
  status: PageStatus;
}

export interface TranslationJob {
  id: string;
  jobId: number;
  title: string;
  inputMode: InputMode;
  sourceType: "pasted_text" | "url";
  sourceUrl?: string;
  sourceLang: SourceLanguage;
  targetLang: TargetLanguage;
  model: string;
  promptVersion: string;
  options: TranslationOptions;
  pages: TranslationPage[];
  currentPageIndex: number;
  status: TranslationStatus;
  createdAt: string;
  updatedAt: string;
}

export interface TranslationApiResult {
  response: TranslationResponse;
  job: TranslationJob;
}

export const DEFAULT_MODEL_SETTINGS: ModelSettings = {
  defaultModel: "gemma4:26b-a4b-it-q4_K_M",
  promptVersion: "translate_ja_ko_v1",
  temperature: 0.3,
  topP: 0.9,
  contextWindow: 8192,
  maxTokens: 4096,
};
