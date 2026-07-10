import { apiRequest } from "@/lib/api/client";
import { detailToJob, historyItemToJob } from "@/lib/api/translationApi";
import type {
  TranslationDetailApiResponse,
  TranslationHistoryApiItem,
  TranslationHistoryItem,
} from "@/types/history";
import type { TranslationJob } from "@/types/translation";

export async function listHistory(): Promise<TranslationHistoryItem[]> {
  const items = await apiRequest<TranslationHistoryApiItem[]>("/api/translations?limit=50&offset=0");
  return items.map(historyApiItemToUiItem);
}

export async function getHistoryDetail(jobId: number): Promise<TranslationJob> {
  const detail = await apiRequest<TranslationDetailApiResponse>(`/api/translations/${jobId}`);
  return detailToJob(detail);
}

export async function deleteHistory(id: string): Promise<void> {
  const jobId = Number(id.replace(/^job-/, ""));
  if (Number.isFinite(jobId)) {
    await apiRequest<void>(`/api/translations/${jobId}`, { method: "DELETE" });
  }
}

export async function clearHistory(): Promise<void> {
  await apiRequest<void>("/api/translations", { method: "DELETE" });
}

function historyApiItemToUiItem(item: TranslationHistoryApiItem): TranslationHistoryItem {
  const job = historyItemToJob(item);
  return {
    id: job.id,
    jobId: job.jobId,
    title: job.title,
    inputMode: job.inputMode,
    sourceUrl: job.sourceUrl,
    sourceSite: job.sourceSite,
    sourceAuthor: job.sourceAuthor,
    sourceWorkId: job.sourceWorkId,
    sourceLang: job.sourceLang,
    targetLang: job.targetLang,
    model: job.model,
    promptVersion: job.promptVersion,
    status: job.status,
    pageCount: item.total_pages,
    translatedCount: item.completed_chunks,
    failedCount: item.failed_chunks,
    sourcePreview: item.source_preview,
    translatedPreview: item.translated_preview ?? "",
    options: job.options,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}
