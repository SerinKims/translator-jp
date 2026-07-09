export type SourceLanguage = "auto" | "ja" | "zh-TW" | "zh-CN" | "en";
export type TargetLanguage = "ko";
export type TranslateScope = "first_page" | "current_page" | "all_pages";
export type InputMode = "url" | "text";
export type ViewerMode = "both" | "translation";
export type TranslationStyle = "webnovel" | "lightnovel" | "literal" | "natural";
export type HonorificPolicy = "preserve" | "naturalize" | "omit";
export type PageStatus = "pending" | "pending_translation" | "in_progress" | "fetched" | "completed" | "failed";
export type TranslationStatus =
  | "idle"
  | "ready"
  | "fetched"
  | "pending_translation"
  | "translating"
  | "completed"
  | "failed"
  | "loaded";

export type OllamaOptionValue = string | number | boolean | null;

export interface ModelSettings {
  defaultModel: string;
  style: TranslationStyle;
  honorificPolicy: HonorificPolicy;
  think: string | boolean;
  temperature: number;
  topP: number;
  contextWindow: number;
  maxTokens: number;
}

export interface TranslationOptions {
  model: string;
  promptVersion?: string;
  style: TranslationStyle;
  honorificPolicy: HonorificPolicy;
  think: string | boolean;
  useGlossary: boolean;
  useCache: boolean;
  preserveNames: boolean;
  temperature: number;
  topP: number;
  contextWindow: number;
  maxTokens: number;
}

export interface TranslationRequest {
  client_options?: TranslationOptions;
  text: string;
  model_name: string;
  prompt_version?: string;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  translate_scope: TranslateScope;
  page_index: number;
  style: TranslationStyle;
  honorific_policy: HonorificPolicy;
  preserve_names: boolean;
  use_glossary: boolean;
  use_cache: boolean;
  stream: false;
  think: string | boolean;
  options: {
    temperature: number;
    top_p: number;
    num_ctx: number;
    num_predict: number;
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
  source_lang: string;
  target_lang: string;
  status: string;
}

export interface TranslationResponse {
  job_id: number;
  source_type: string;
  source_lang: string;
  target_lang: string;
  current_page_index: number;
  total_pages: number;
  has_next_page: boolean;
  translated_text: string;
  model: string;
  prompt_version: string;
  style: string;
  elapsed_ms: number;
  cache_hit: boolean;
  chunks: TranslationChunkResponse[];
}

export interface TranslationPage {
  index: number;
  id?: number;
  title?: string | null;
  sourceText: string;
  translatedText: string;
  status: PageStatus;
  totalChunks?: number;
  completedChunks?: number;
  failedChunks?: number;
  errorMessage?: string | null;
}

export interface TranslationChunk {
  id: number;
  pageId: number;
  pageIndex: number | null;
  index: number;
  sourceText: string;
  translatedText: string;
  status: string;
  retryCount: number;
  errorMessage: string | null;
}

export interface TranslationJob {
  id: string;
  jobId: number;
  title: string;
  inputMode: InputMode;
  sourceType: "pasted_text" | "url";
  sourceUrl?: string;
  sourceSite?: string;
  sourceAuthor?: string | null;
  sourceWorkId?: string | null;
  sourceFetchedAt?: string | null;
  sourceLang: SourceLanguage;
  targetLang: TargetLanguage;
  model: string;
  promptVersion: string;
  options: TranslationOptions;
  pages: TranslationPage[];
  chunks: TranslationChunk[];
  currentPageIndex: number;
  status: TranslationStatus;
  sourcePreview?: string;
  translatedPreview?: string;
  errorMessage?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TranslationApiResult {
  response: TranslationResponse;
  job: TranslationJob;
}

export const DEFAULT_MODEL_SETTINGS: ModelSettings = {
  defaultModel: "gemma4:26b-a4b-it-q4_K_M",
  style: "webnovel",
  honorificPolicy: "preserve",
  think: false,
  temperature: 0.3,
  topP: 0.9,
  contextWindow: 8192,
  maxTokens: 4096,
};
