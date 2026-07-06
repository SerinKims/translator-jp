import type { SourceLanguage, TargetLanguage } from "@/types/translation";

export type GlossarySourceLanguage = Exclude<SourceLanguage, "auto">;
export type GlossaryTermType = "common" | "person" | "place" | "title" | "skill" | "organization" | "honorific" | "proper_noun";

export interface GlossaryTerm {
  id: number;
  glossary_set_id: number | null;
  source_lang: GlossarySourceLanguage;
  target_lang: TargetLanguage;
  source_term: string;
  target_term: string;
  term_type: GlossaryTermType;
  description: string | null;
  aliases: string[];
  priority: number;
  is_required: boolean;
  is_case_sensitive: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GlossaryTermCreateRequest {
  glossary_set_id?: number | null;
  source_lang: GlossarySourceLanguage;
  target_lang: TargetLanguage;
  source_term: string;
  target_term: string;
  term_type: GlossaryTermType;
  description?: string | null;
  aliases?: string[];
  priority: number;
  is_required: boolean;
  is_case_sensitive: boolean;
  is_active: boolean;
}

export type GlossaryTermUpdateRequest = Partial<GlossaryTermCreateRequest>;

export interface GlossaryImportRequest {
  text: string;
}

export interface GlossaryImportConflict {
  row: number;
  source_lang: GlossarySourceLanguage;
  target_lang: TargetLanguage;
  source_term: string;
  target_term: string;
  message: string;
}

export interface GlossaryImportResponse {
  imported: number;
  skipped_duplicates: number;
  conflicts: GlossaryImportConflict[];
}

export interface GlossaryCandidate {
  id: number;
  source_lang: GlossarySourceLanguage;
  target_lang: TargetLanguage;
  source_term: string;
  suggested_target_term: string;
  source_text: string;
  model_translation: string;
  user_corrected_translation: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface GlossaryCandidateApproveRequest {
  glossary_set_id?: number | null;
  term_type: GlossaryTermType;
  description?: string | null;
  aliases?: string[];
  priority: number;
  is_required: boolean;
  is_case_sensitive: boolean;
}
