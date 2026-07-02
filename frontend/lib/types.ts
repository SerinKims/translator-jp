export type SourceLang = "auto" | "ja" | "zh-CN" | "zh-TW" | "en"
export type TargetLang = "ko"
export type TranslateScope = "first_page" | "current_page" | "all_pages"
export type ViewMode = "parallel" | "translation_only"
export type ChunkStatus = "pending" | "running" | "completed" | "failed" | "skipped"

export type TranslationOptions = {
  source_lang: SourceLang
  target_lang: TargetLang
  translate_scope: TranslateScope
  page_index: number
  style: string
  honorific_policy: string
  preserve_names: boolean
  use_glossary: boolean
  use_cache: boolean
  stream: boolean
}

export type TranslateRequest = TranslationOptions & {
  text: string
}

export type PixivTranslateRequest = TranslationOptions & {
  url: string
}

export type PageTranslateRequest = Omit<TranslationOptions, "translate_scope" | "page_index"> & {
  translate_scope: "current_page"
  force?: boolean
}

export type TranslationChunk = {
  index: number
  source_text: string
  translated_text: string | null
  status: ChunkStatus
  error_message?: string | null
}

export type ApiTranslationChunk = {
  index: number
  source_lang: string
  target_lang: string
  status: string
}

export type TranslationResponse = {
  job_id: number
  source_type?: string
  source_site?: string | null
  source_url?: string | null
  source_work_id?: string | null
  title?: string | null
  author?: string | null
  source_lang?: string
  target_lang?: string
  current_page_index: number
  total_pages: number
  has_next_page: boolean
  translated_text: string
  model: string
  prompt_version: string
  style?: string
  elapsed_ms: number
  cache_hit?: boolean
  chunks: ApiTranslationChunk[]
}

export type TranslationHistoryItem = {
  job_id: number
  source_site: string
  source_url: string | null
  source_title: string | null
  source_author: string | null
  source_work_id: string | null
  source_fetched_at: string | null
  source_preview: string
  translated_preview: string | null
  source_lang: string
  target_lang: string
  model_name: string
  prompt_version: string
  ollama_think: string | null
  ollama_options_json: string | null
  style: string
  honorific_policy: string
  preserve_names: boolean
  status: string
  total_pages: number
  total_chunks: number
  completed_chunks: number
  failed_chunks: number
  elapsed_ms: number | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type TranslationPageHistory = {
  id: number
  page_index: number
  page_title: string | null
  source_text: string
  translated_text: string | null
  status: string
  total_chunks: number
  completed_chunks: number
  failed_chunks: number
  elapsed_ms: number | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type TranslationChunkHistory = {
  id: number
  page_id: number
  page_index: number | null
  chunk_index: number
  source_lang: string
  target_lang: string
  source_text: string
  translated_text: string | null
  context_before: string | null
  context_after: string | null
  status: ChunkStatus
  retry_count: number
  prompt_used: string | null
  raw_model_response: string | null
  elapsed_ms: number | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type TranslationDetailResponse = TranslationHistoryItem & {
  original_text: string
  translated_text: string | null
  pages: TranslationPageHistory[]
  chunks: TranslationChunkHistory[]
}

export type GlossaryTerm = {
  id: number
  source_lang: SourceLang | string
  target_lang: TargetLang | string
  source_term: string
  target_term: string
  term_type: string
  description: string | null
  aliases: string[]
  priority: number
  is_required: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export type GlossaryTermInput = {
  source_lang: SourceLang
  target_lang: TargetLang
  source_term: string
  target_term: string
  term_type: string
  description: string | null
  aliases: string[]
  priority: number
  is_required: boolean
  is_active?: boolean
}

export type GlossaryImportResponse = {
  imported: number
  skipped_duplicates: number
  conflicts: Array<{
    row: number
    source_lang: string
    target_lang: string
    source_term: string
    target_term: string
    message: string
  }>
}

export type GlossaryCandidate = {
  id: number
  source_lang: string
  target_lang: string
  source_term: string
  suggested_target_term: string
  source_text: string
  model_translation: string
  user_corrected_translation: string
  status: "pending" | "approved" | "rejected"
  created_at: string
  updated_at: string
}
