"use client"

import { AlertCircle, Loader2 } from "lucide-react"
import type { ReactNode } from "react"
import type { TranslationChunk, ViewMode } from "@/lib/types"
import { sortChunks } from "@/lib/translation-utils"
import { cn } from "@/lib/utils"

type ParallelTranslationViewProps = {
  chunks: TranslationChunk[]
  viewMode: ViewMode
}

export function ParallelTranslationView({
  chunks,
  viewMode,
}: ParallelTranslationViewProps) {
  const sortedChunks = sortChunks(chunks)

  if (sortedChunks.length === 0) {
    return (
      <div className="rounded-lg border border-[#d9d9dd] px-4 py-10 text-center text-sm text-[#75758a]">
        번역 결과가 아직 없습니다.
      </div>
    )
  }

  if (viewMode === "translation_only") {
    return <ReaderView chunks={sortedChunks} />
  }

  return (
    <div className="space-y-3">
      {sortedChunks.map((chunk) => (
        <article key={chunk.index} className="border-t border-[#e5e5e8] pt-4">
          <div className="mb-2 font-mono text-xs uppercase tracking-[0.04em] text-[#75758a]">
            Chunk {chunk.index + 1}
          </div>
          <div className={cn("grid gap-4", viewMode === "parallel" && "lg:grid-cols-2")}>
            <TextPane title="원문" text={chunk.source_text} />
            <TextPane title="번역" text={renderTranslationText(chunk)} />
          </div>
        </article>
      ))}
    </div>
  )
}

function ReaderView({ chunks }: { chunks: TranslationChunk[] }) {
  return (
    <article
      aria-label="번역문"
      className="mx-auto max-w-[840px] border-y border-[#d9d9dd] py-7"
    >
      <div className="space-y-7 text-[17px] leading-9 text-[#17171c]">
        {chunks.map((chunk) => (
          <div
            key={chunk.index}
            className="whitespace-pre-wrap break-words"
            data-testid="reader-chunk"
          >
            {renderTranslationText(chunk)}
          </div>
        ))}
      </div>
    </article>
  )
}

function TextPane({ title, text }: { title: string; text: ReactNode }) {
  return (
    <section className="min-h-40 border-l border-[#d9d9dd] bg-white pl-4">
      <div className="mb-2 text-xs font-medium uppercase tracking-[0.04em] text-[#75758a]">
        {title}
      </div>
      <div className="max-h-[520px] overflow-auto whitespace-pre-wrap break-words pr-3 text-sm leading-7 text-[#212121]">
        {text}
      </div>
    </section>
  )
}

function renderTranslationText(chunk: TranslationChunk) {
  if (chunk.status === "failed") {
    return (
      <span className="flex flex-col gap-2 text-[#b30000]">
        <span className="flex items-center gap-2 font-medium">
          <AlertCircle aria-hidden className="h-4 w-4" />
          번역 실패
        </span>
        <span>{chunk.error_message ?? "오류 메시지가 없습니다."}</span>
      </span>
    )
  }

  if (chunk.status === "running") {
    return (
      <span className="flex items-center gap-2 text-[#75758a]">
        <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
        번역 중...
      </span>
    )
  }

  if (chunk.status === "pending") {
    return <span className="text-[#75758a]">대기 중...</span>
  }

  if (chunk.status === "skipped") {
    return <span className="text-[#75758a]">건너뜀</span>
  }

  return chunk.translated_text || "모델이 빈 응답을 반환했습니다. 다시 시도해주세요."
}
