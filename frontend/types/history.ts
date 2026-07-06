import type { InputMode, SourceLanguage, TargetLanguage, TranslationOptions, TranslationPage } from "@/types/translation";

export interface TranslationHistoryItem {
  id: string;
  jobId: number;
  title: string;
  inputMode: InputMode;
  sourceUrl?: string;
  sourceLang: SourceLanguage;
  targetLang: TargetLanguage;
  model: string;
  promptVersion: string;
  pageCount: number;
  translatedCount: number;
  sourcePreview: string;
  translatedPreview: string;
  options: TranslationOptions;
  pages: TranslationPage[];
  createdAt: string;
  updatedAt: string;
}
