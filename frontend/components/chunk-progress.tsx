"use client"

import { Activity } from "lucide-react"
import type { TranslationChunk } from "@/lib/types"

type ChunkProgressProps = {
  chunks: TranslationChunk[]
  totalPages?: number
  currentPageIndex?: number
}

export function ChunkProgress({
  chunks,
  totalPages,
  currentPageIndex,
}: ChunkProgressProps) {
  const completed = chunks.filter((chunk) => chunk.status === "completed").length
  const failed = chunks.filter((chunk) => chunk.status === "failed").length
  const total = chunks.length
  const pageText =
    totalPages && totalPages > 0
      ? `Page ${(currentPageIndex ?? 0) + 1} / ${totalPages}`
      : "Page 1 / 1"

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#75758a]">
      <span className="flex items-center gap-1.5 font-medium text-[#212121]">
        <Activity aria-hidden className="h-4 w-4" />
        진행
      </span>
      <span>{pageText}</span>
      <span>Chunk {total === 0 ? "0 / 0" : `${completed} / ${total}`}</span>
      {failed > 0 ? <span className="text-[#b30000]">실패 {failed}</span> : null}
    </div>
  )
}
