import type { SourceLanguage, TargetLanguage } from "@/types/translation";

export type GlossaryTermType = "person" | "place" | "skill" | "proper_noun" | "common";

export interface GlossaryTerm {
  id: number;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  source_term: string;
  target_term: string;
  term_type: GlossaryTermType;
  description: string | null;
  aliases: string[];
  priority: number;
  is_required: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GlossaryTermCreateRequest {
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  source_term: string;
  target_term: string;
  term_type: GlossaryTermType;
  description?: string | null;
  aliases?: string[];
  priority: number;
  is_required: boolean;
  is_active: boolean;
}

export type GlossaryTermUpdateRequest = Partial<GlossaryTermCreateRequest>;
