import type {
  InputMode,
  SourceLanguage,
  TargetLanguage,
  TranslationOptions,
  TranslationPage,
  TranslationStatus,
} from "@/types/translation";

export interface TranslationHistoryApiItem {
  job_id: number;
  source_site: string;
  source_url: string | null;
  source_title: string | null;
  source_author: string | null;
  source_work_id: string | null;
  source_fetched_at: string | null;
  source_preview: string;
  translated_preview: string | null;
  source_lang: string;
  target_lang: string;
  model_name: string;
  prompt_version: string;
  ollama_think: string | null;
  ollama_options_json: string | null;
  style: string;
  honorific_policy: string;
  preserve_names: boolean;
  status: string;
  total_pages: number;
  total_chunks: number;
  completed_chunks: number;
  failed_chunks: number;
  elapsed_ms: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranslationPageHistoryApiItem {
  id: number;
  page_index: number;
  page_title: string | null;
  source_text: string;
  translated_text: string | null;
  status: string;
  total_chunks: number;
  completed_chunks: number;
  failed_chunks: number;
  elapsed_ms: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranslationChunkHistoryApiItem {
  id: number;
  page_id: number;
  page_index: number | null;
  chunk_index: number;
  source_lang: string;
  target_lang: string;
  source_text: string;
  translated_text: string | null;
  context_before: string | null;
  context_after: string | null;
  status: string;
  retry_count: number;
  prompt_used: string | null;
  raw_model_response: string | null;
  elapsed_ms: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranslationDetailApiResponse extends TranslationHistoryApiItem {
  original_text: string;
  translated_text: string | null;
  pages: TranslationPageHistoryApiItem[];
  chunks: TranslationChunkHistoryApiItem[];
}

export interface TranslationHistoryItem {
  id: string;
  jobId: number;
  title: string;
  inputMode: InputMode;
  sourceUrl?: string;
  sourceSite?: string;
  sourceAuthor?: string | null;
  sourceWorkId?: string | null;
  sourceLang: SourceLanguage;
  targetLang: TargetLanguage;
  model: string;
  promptVersion: string;
  status: TranslationStatus;
  pageCount: number;
  translatedCount: number;
  failedCount: number;
  sourcePreview: string;
  translatedPreview: string;
  options: TranslationOptions;
  pages?: TranslationPage[];
  createdAt: string;
  updatedAt: string;
}
