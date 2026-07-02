"use client"

import {
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardCopy,
  FastForward,
  Layers,
  Play,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ChunkProgress } from "@/components/chunk-progress"
import { ParallelTranslationView } from "@/components/parallel-translation-view"
import { ViewModeToggle } from "@/components/view-mode-toggle"
import type { TranslationChunk, TranslationDetailResponse, ViewMode } from "@/lib/types"
import {
  formatSourceAndTranslation,
  formatTranslationOnly,
} from "@/lib/translation-utils"

type TranslationResultProps = {
  detail: TranslationDetailResponse | null
  chunks: TranslationChunk[]
  currentPageIndex: number
  viewMode: ViewMode
  onViewModeChange: (value: ViewMode) => void
  onPageChange: (pageIndex: number) => void
  onTranslateCurrentPage: () => void
  onTranslateAllPages: () => void
  isWorking?: boolean
  copiedMessage?: string | null
  onCopy: (value: string) => void
}

export function TranslationResult({
  detail,
  chunks,
  currentPageIndex,
  viewMode,
  onViewModeChange,
  onPageChange,
  onTranslateCurrentPage,
  onTranslateAllPages,
  isWorking,
  copiedMessage,
  onCopy,
}: TranslationResultProps) {
  const hasMultiplePages = (detail?.total_pages ?? 1) > 1
  const canGoPrevious = hasMultiplePages && currentPageIndex > 0
  const canGoNext =
    hasMultiplePages && detail != null && currentPageIndex < detail.total_pages - 1
  const currentPage = detail?.pages.find(
    (page) => page.page_index === currentPageIndex,
  )
  const canTranslateCurrentPage =
    detail != null && currentPage != null && currentPage.status !== "completed"

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[#d9d9dd] pb-3">
        <div>
          <h2 className="text-xl font-semibold text-[#17171c]">번역 결과</h2>
          <div className="mt-2">
            <ChunkProgress
              chunks={chunks}
              totalPages={detail?.total_pages}
              currentPageIndex={currentPageIndex}
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ViewModeToggle value={viewMode} onChange={onViewModeChange} />
          <Button
            variant="outline"
            disabled={chunks.length === 0}
            onClick={() => onCopy(formatTranslationOnly(chunks))}
          >
            <ClipboardCopy aria-hidden className="h-4 w-4" />
            번역문 복사
          </Button>
          <Button
            variant="outline"
            disabled={chunks.length === 0}
            onClick={() => onCopy(formatSourceAndTranslation(chunks))}
          >
            <Layers aria-hidden className="h-4 w-4" />
            원문+번역 복사
          </Button>
          {hasMultiplePages ? (
            <>
              <Button
                variant="outline"
                disabled={isWorking || !canGoPrevious}
                onClick={() => onPageChange(currentPageIndex - 1)}
              >
                <ChevronLeft aria-hidden className="h-4 w-4" />
                이전 페이지
              </Button>
              <Button
                variant="outline"
                disabled={isWorking || !canGoNext}
                onClick={() => onPageChange(currentPageIndex + 1)}
              >
                <ChevronRight aria-hidden className="h-4 w-4" />
                다음 페이지
              </Button>
            </>
          ) : null}
          {canTranslateCurrentPage ? (
            <Button disabled={isWorking} onClick={onTranslateCurrentPage}>
              <Play aria-hidden className="h-4 w-4" />
              현재 페이지 번역
            </Button>
          ) : null}
          {hasMultiplePages ? (
            <Button variant="outline" disabled={isWorking} onClick={onTranslateAllPages}>
              <FastForward aria-hidden className="h-4 w-4" />
              전체 번역
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex min-h-6 flex-wrap items-center gap-3 text-sm text-[#75758a]">
        {hasMultiplePages ? (
          <span>
            총 {detail?.total_pages}개 페이지가 감지되었습니다. 페이지를 이동해
            원문을 확인하고 필요한 페이지를 번역할 수 있습니다.
          </span>
        ) : null}
        {copiedMessage ? (
          <span className="inline-flex items-center gap-2 text-[#003c33]">
            <Check aria-hidden className="h-4 w-4" />
            {copiedMessage}
          </span>
        ) : null}
      </div>

      <ParallelTranslationView chunks={chunks} viewMode={viewMode} />
    </section>
  )
}
