"use client"

import { Clock3, RefreshCw } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { getTranslationDetail, listTranslations } from "@/lib/api"
import type { TranslationDetailResponse } from "@/lib/types"

type HistoryListProps = {
  onSelect: (detail: TranslationDetailResponse) => void
}

export function HistoryList({ onSelect }: HistoryListProps) {
  const historyQuery = useQuery({
    queryKey: ["translations"],
    queryFn: () => listTranslations(20),
  })

  const openDetail = async (jobId: number) => {
    const detail = await getTranslationDetail(jobId)
    onSelect(detail)
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-xl font-medium">
          <Clock3 aria-hidden className="h-5 w-5" />
          번역 이력
        </h2>
        <Button
          variant="ghost"
          className="min-h-9 px-3"
          onClick={() => historyQuery.refetch()}
        >
          <RefreshCw aria-hidden className="h-4 w-4" />
          새로고침
        </Button>
      </div>

      {historyQuery.isLoading ? (
        <p className="text-sm text-[#75758a]">번역 이력을 불러오는 중입니다...</p>
      ) : null}
      {historyQuery.error ? (
        <p className="text-sm text-[#b30000]">
          번역 이력을 불러오지 못했습니다.
        </p>
      ) : null}
      {historyQuery.data?.length === 0 ? (
        <p className="text-sm text-[#75758a]">아직 저장된 번역 이력이 없습니다.</p>
      ) : null}

      <div className="space-y-2">
        {historyQuery.data?.map((item) => (
          <button
            key={item.job_id}
            type="button"
            className="w-full rounded-lg border border-[#d9d9dd] bg-white px-3 py-3 text-left transition-colors hover:border-[#17171c]"
            onClick={() => void openDetail(item.job_id)}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-medium">
                {item.source_title || item.source_preview || `Job ${item.job_id}`}
              </span>
              <span className="font-mono text-xs uppercase text-[#75758a]">
                {item.status}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-[#75758a]">
              <span>{item.source_site}</span>
              <span>{new Date(item.created_at).toLocaleString("ko-KR")}</span>
              <span>{item.total_pages} page</span>
            </div>
          </button>
        ))}
      </div>
    </section>
  )
}
