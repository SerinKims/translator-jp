import { apiRequest } from "@/lib/api/client";
import { detailToJob, historyItemToJob } from "@/lib/api/translationApi";
import type {
  TranslationDetailApiResponse,
  TranslationHistoryApiItem,
  TranslationHistoryItem,
} from "@/types/history";
import type { TranslationJob } from "@/types/translation";

const HIDDEN_HISTORY_KEY = "translator-hidden-history-job-ids-v1";

export async function listHistory(): Promise<TranslationHistoryItem[]> {
  const items = await apiRequest<TranslationHistoryApiItem[]>("/api/translations?limit=50&offset=0");
  const hiddenIds = readHiddenHistoryIds();
  return items.filter((item) => !hiddenIds.includes(item.job_id)).map(historyApiItemToUiItem);
}

export async function getHistoryDetail(jobId: number): Promise<TranslationJob> {
  const detail = await apiRequest<TranslationDetailApiResponse>(`/api/translations/${jobId}`);
  return detailToJob(detail);
}

export async function deleteHistory(id: string): Promise<void> {
  // Backend API.md currently has no history delete endpoint.
  // Keep the UI behavior by hiding the job locally until a real DELETE endpoint exists.
  const jobId = Number(id.replace(/^job-/, ""));
  if (Number.isFinite(jobId)) {
    writeHiddenHistoryIds([...new Set([...readHiddenHistoryIds(), jobId])]);
  }
}

export async function clearHistory(): Promise<void> {
  const items = await apiRequest<TranslationHistoryApiItem[]>("/api/translations?limit=100&offset=0");
  writeHiddenHistoryIds([...new Set([...readHiddenHistoryIds(), ...items.map((item) => item.job_id)])]);
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

function readHiddenHistoryIds(): number[] {
  if (typeof window === "undefined") {
    return [];
  }
  const value = window.localStorage.getItem(HIDDEN_HISTORY_KEY);
  if (!value) {
    return [];
  }
  try {
    const parsed = JSON.parse(value) as unknown;
    return Array.isArray(parsed) ? parsed.filter((item): item is number => typeof item === "number") : [];
  } catch {
    return [];
  }
}

function writeHiddenHistoryIds(ids: number[]): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(HIDDEN_HISTORY_KEY, JSON.stringify(ids));
}
