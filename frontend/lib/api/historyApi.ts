import { delay } from "@/lib/api/storage";
import { getStoredJobs, saveStoredJobs } from "@/lib/api/translationApi";
import type { TranslationHistoryItem } from "@/types/history";

export async function listHistory(): Promise<TranslationHistoryItem[]> {
  await delay(100);
  return getStoredJobs().map((job) => {
    const firstTranslated = job.pages.find((page) => page.translatedText)?.translatedText ?? "";
    return {
      id: job.id,
      jobId: job.jobId,
      title: job.title,
      inputMode: job.inputMode,
      sourceUrl: job.sourceUrl,
      sourceLang: job.sourceLang,
      targetLang: job.targetLang,
      model: job.model,
      promptVersion: job.promptVersion,
      pageCount: job.pages.length,
      translatedCount: job.pages.filter((page) => page.status === "completed").length,
      sourcePreview: job.pages[0]?.sourceText.slice(0, 120) ?? "",
      translatedPreview: firstTranslated.slice(0, 120),
      options: job.options,
      pages: job.pages,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
    };
  });
}

export async function deleteHistory(id: string) {
  await delay(100);
  saveStoredJobs(getStoredJobs().filter((job) => job.id !== id));
}

export async function clearHistory() {
  await delay(100);
  saveStoredJobs([]);
}
