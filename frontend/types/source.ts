import type {
  HonorificPolicy,
  SourceLanguage,
  TargetLanguage,
  TranslateScope,
  TranslationChunkResponse,
  TranslationStyle,
} from "@/types/translation";

export interface PixivFetchRequest {
  url: string;
  translate_after_fetch?: boolean;
  model_name?: string;
  prompt_version?: string;
  source_lang?: SourceLanguage;
  target_lang?: TargetLanguage;
  style?: TranslationStyle;
  honorific_policy?: HonorificPolicy;
  preserve_names?: boolean;
  think?: string | boolean;
  options?: Record<string, string | number | boolean | null>;
}

export interface PixivFetchResponse {
  source_site: string;
  source_url: string;
  source_work_id: string;
  title: string;
  author: string;
  text: string;
  char_count: number;
  job_id: number;
}

export interface PixivTranslateRequest {
  url: string;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  translate_scope: TranslateScope;
  page_index: number;
  model_name: string;
  prompt_version?: string;
  style: TranslationStyle;
  honorific_policy: HonorificPolicy;
  preserve_names: boolean;
  use_glossary: boolean;
  use_cache: boolean;
  stream: false;
  think: string | boolean;
  options?: Record<string, string | number | boolean | null>;
}

export interface PixivTranslateResponse {
  job_id: number;
  source_site: string;
  source_url: string;
  source_work_id: string;
  title: string;
  author: string;
  current_page_index: number;
  total_pages: number;
  has_next_page: boolean;
  translated_text: string;
  model: string;
  prompt_version: string;
  elapsed_ms: number;
  chunks: TranslationChunkResponse[];
}
