"use client"

import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  Clock3,
  Loader2,
  Play,
  Settings2,
} from "lucide-react"
import type { ReactNode } from "react"
import { useMemo, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { GlossaryManager } from "@/components/glossary-manager"
import { HistoryList } from "@/components/history-list"
import { PixivUrlInput } from "@/components/pixiv-url-input"
import { SourceTextInput } from "@/components/source-text-input"
import { Button } from "@/components/ui/button"
import { TranslationOptionsPanel } from "@/components/translation-options"
import { TranslationResult } from "@/components/translation-result"
import {
  getTranslationDetail,
  translatePage,
  translatePixiv,
  translateText,
} from "@/lib/api"
import type { TranslationDetailResponse, TranslationOptions, ViewMode } from "@/lib/types"
import {
  chooseTranslationRoute,
  chunksForPage,
  defaultTranslationOptions,
  toPageTranslateRequest,
} from "@/lib/translation-utils"

const validationMessage = "pixiv URL 또는 번역할 텍스트를 입력해주세요."

export default function HomePage() {
  const queryClient = useQueryClient()
  const [pixivUrl, setPixivUrl] = useState("")
  const [sourceText, setSourceText] = useState("")
  const [options, setOptions] = useState<TranslationOptions>(defaultTranslationOptions)
  const [viewMode, setViewMode] = useState<ViewMode>("translation_only")
  const [detail, setDetail] = useState<TranslationDetailResponse | null>(null)
  const [visiblePageIndex, setVisiblePageIndex] = useState(0)
  const [statusText, setStatusText] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [copiedMessage, setCopiedMessage] = useState<string | null>(null)
  const [isWorking, setIsWorking] = useState(false)

  const chunks = useMemo(
    () => chunksForPage(detail, visiblePageIndex),
    [detail, visiblePageIndex],
  )

  const handleTranslate = async () => {
    const route = chooseTranslationRoute(pixivUrl, sourceText)
    setErrorMessage(null)
    setCopiedMessage(null)

    if (route === "empty") {
      setErrorMessage(validationMessage)
      return
    }

    setIsWorking(true)
    try {
      if (route === "pixiv") {
        setStatusText("원문을 가져오는 중입니다...")
        setStatusText("번역을 준비하는 중입니다...")
        const response = await translatePixiv({
          ...options,
          url: pixivUrl.trim(),
          translate_scope: "first_page",
          page_index: 0,
        })
        setStatusText("번역 중입니다...")
        await loadDetail(response.job_id, response.current_page_index)
      } else {
        setStatusText("번역을 준비하는 중입니다...")
        const response = await translateText({
          ...options,
          text: sourceText,
          translate_scope: "first_page",
          page_index: 0,
        })
        setStatusText("번역 중입니다...")
        await loadDetail(response.job_id, response.current_page_index)
      }
      setStatusText("번역이 완료되었습니다.")
      await queryClient.invalidateQueries({ queryKey: ["translations"] })
    } catch (error) {
      setStatusText(null)
      setErrorMessage(error instanceof Error ? error.message : "번역 요청에 실패했습니다.")
    } finally {
      setIsWorking(false)
    }
  }

  const loadDetail = async (jobId: number, pageIndex = 0) => {
    const nextDetail = await getTranslationDetail(jobId)
    setDetail(nextDetail)
    setVisiblePageIndex(pageIndex)
  }

  const handlePageChange = (pageIndex: number) => {
    if (!detail) {
      return
    }
    const nextPageIndex = Math.min(Math.max(pageIndex, 0), detail.total_pages - 1)
    setVisiblePageIndex(nextPageIndex)
    setCopiedMessage(null)
    setErrorMessage(null)
  }

  const handleTranslateCurrentPage = async () => {
    if (!detail) {
      return
    }
    await translateSelectedPage(detail.job_id, visiblePageIndex)
  }

  const handleTranslateAllPages = async () => {
    if (!detail) {
      return
    }
    const confirmed = window.confirm(
      "전체 page를 번역하면 시간이 오래 걸릴 수 있습니다. 계속하시겠습니까?",
    )
    if (!confirmed) {
      return
    }

    const remainingPages = detail.pages
      .filter(
        (page) => page.page_index >= visiblePageIndex && page.status !== "completed",
      )
      .sort((left, right) => left.page_index - right.page_index)
    for (const page of remainingPages) {
      await translateSelectedPage(detail.job_id, page.page_index)
    }
  }

  const translateSelectedPage = async (jobId: number, pageIndex: number) => {
    if (!detail) {
      return
    }
    setIsWorking(true)
    setErrorMessage(null)
    try {
      setStatusText("번역 중입니다...")
      await translatePage(
        jobId,
        pageIndex,
        toPageTranslateRequest(options, detail.source_lang, detail.target_lang),
      )
      await loadDetail(jobId, pageIndex)
      setStatusText("번역이 완료되었습니다.")
      await queryClient.invalidateQueries({ queryKey: ["translations"] })
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "page 번역 요청에 실패했습니다.",
      )
    } finally {
      setIsWorking(false)
    }
  }

  const handleCopy = async (value: string) => {
    if (!value.trim()) {
      setErrorMessage("복사할 번역 결과가 없습니다.")
      return
    }
    await navigator.clipboard.writeText(value)
    setCopiedMessage("복사되었습니다.")
    window.setTimeout(() => setCopiedMessage(null), 2_000)
  }

  const handleHistorySelect = (nextDetail: TranslationDetailResponse) => {
    setDetail(nextDetail)
    setVisiblePageIndex(
      nextDetail.pages.find((page) => page.status === "completed")?.page_index ??
        nextDetail.pages[0]?.page_index ??
        0,
    )
    setViewMode("translation_only")
    setErrorMessage(null)
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-end justify-between gap-3 border-b border-[#d9d9dd] pb-4">
          <div>
            <h1 className="text-2xl font-semibold leading-tight text-[#17171c]">
              translator-jp
            </h1>
            <p className="mt-1 text-sm text-[#75758a]">
              일본어 원문과 pixiv 소설 URL을 한국어 웹소설 문체로 번역합니다.
            </p>
          </div>
          <p className="font-mono text-xs uppercase tracking-[0.04em] text-[#75758a]">
            Local Ollama
          </p>
        </header>

        <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-7">
            <section className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-[#17171c]">번역 입력</h2>
                <p className="mt-1 text-sm text-[#75758a]">
                  pixiv URL이 있으면 URL을 우선 사용하고, 없으면 직접 입력한 원문을
                  번역합니다.
                </p>
              </div>
              <PixivUrlInput
                value={pixivUrl}
                disabled={isWorking}
                onChange={setPixivUrl}
              />
              <SourceTextInput
                value={sourceText}
                disabled={isWorking}
                onChange={setSourceText}
              />
              <CollapsiblePanel
                title="번역 설정"
                icon={<Settings2 aria-hidden className="h-4 w-4" />}
              >
                <TranslationOptionsPanel
                  options={options}
                  disabled={isWorking}
                  onChange={setOptions}
                />
              </CollapsiblePanel>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  className="min-h-12 px-7"
                  disabled={isWorking}
                  onClick={() => void handleTranslate()}
                >
                  {isWorking ? (
                    <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play aria-hidden className="h-4 w-4" />
                  )}
                  번역 실행
                </Button>
                {statusText ? (
                  <span className="text-sm text-[#003c33]">{statusText}</span>
                ) : null}
              </div>
              {errorMessage ? (
                <div className="flex items-start gap-2 rounded-lg border border-[#b30000] px-3 py-3 text-sm text-[#b30000]">
                  <AlertCircle aria-hidden className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              ) : null}
            </section>

            <TranslationResult
              detail={detail}
              chunks={chunks}
              currentPageIndex={visiblePageIndex}
              viewMode={viewMode}
              isWorking={isWorking}
              copiedMessage={copiedMessage}
              onViewModeChange={setViewMode}
              onPageChange={handlePageChange}
              onTranslateCurrentPage={() => void handleTranslateCurrentPage()}
              onTranslateAllPages={() => void handleTranslateAllPages()}
              onCopy={(value) => void handleCopy(value)}
            />
          </div>

          <aside className="space-y-5">
            <CollapsiblePanel
              title="번역 이력"
              icon={<Clock3 aria-hidden className="h-4 w-4" />}
            >
              <HistoryList onSelect={handleHistorySelect} />
            </CollapsiblePanel>
            <CollapsiblePanel
              title="용어집"
              icon={<BookOpen aria-hidden className="h-4 w-4" />}
            >
              <GlossaryManager />
            </CollapsiblePanel>
          </aside>
        </div>
      </div>
    </main>
  )
}

function CollapsiblePanel({
  title,
  icon,
  children,
}: {
  title: string
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <details className="group border-y border-[#d9d9dd] py-3">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-medium text-[#17171c] marker:hidden">
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        <ChevronDown
          aria-hidden
          className="h-4 w-4 text-[#75758a] transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="pt-4">{children}</div>
    </details>
  )
}
