import type {
  PageTranslateRequest,
  SourceLang,
  TargetLang,
  TranslationChunk,
  TranslationDetailResponse,
  TranslationOptions,
} from "@/lib/types"

export const defaultTranslationOptions: TranslationOptions = {
  source_lang: "ja",
  target_lang: "ko",
  translate_scope: "first_page",
  page_index: 0,
  style: "webnovel",
  honorific_policy: "preserve",
  preserve_names: true,
  use_glossary: true,
  use_cache: true,
  stream: false,
}

export type TranslationRoute = "pixiv" | "text" | "empty"

export function chooseTranslationRoute(pixivUrl: string, sourceText: string): TranslationRoute {
  if (pixivUrl.trim()) {
    return "pixiv"
  }
  if (sourceText.trim()) {
    return "text"
  }
  return "empty"
}

export function nextPageIndex(currentPageIndex: number) {
  return currentPageIndex + 1
}

export function previousPageIndex(currentPageIndex: number) {
  return Math.max(0, currentPageIndex - 1)
}

export function toPageTranslateRequest(
  options: TranslationOptions,
  sourceLang?: SourceLang | string,
  targetLang?: TargetLang | string,
): PageTranslateRequest {
  return {
    source_lang: normalizeSourceLang(sourceLang ?? options.source_lang),
    target_lang: targetLang === "ko" ? "ko" : options.target_lang,
    translate_scope: "current_page",
    style: options.style,
    honorific_policy: options.honorific_policy,
    preserve_names: options.preserve_names,
    use_glossary: options.use_glossary,
    use_cache: options.use_cache,
    stream: false,
    force: false,
  }
}

export function chunksForPage(
  detail: TranslationDetailResponse | null | undefined,
  pageIndex?: number,
): TranslationChunk[] {
  if (!detail) {
    return []
  }

  const selectedPageIndex =
    pageIndex ??
    detail.pages.find((page) => page.status === "completed")?.page_index ??
    detail.pages[0]?.page_index ??
    0

  const pageChunks = detail.chunks
    .filter((chunk) => chunk.page_index === selectedPageIndex)
    .map((chunk) => ({
      index: chunk.chunk_index,
      source_text: chunk.source_text,
      translated_text: chunk.translated_text,
      status: chunk.status,
      error_message: chunk.error_message,
    }))

  if (pageChunks.length > 0) {
    return sortChunks(pageChunks)
  }

  const page = detail.pages.find((item) => item.page_index === selectedPageIndex)
  if (!page) {
    return []
  }

  return [
    {
      index: 0,
      source_text: page.source_text,
      translated_text: page.translated_text,
      status: page.status === "completed" ? "completed" : "pending",
      error_message: page.error_message,
    },
  ]
}

export function sortChunks(chunks: TranslationChunk[]) {
  return [...chunks].sort((left, right) => left.index - right.index)
}

export function formatTranslationOnly(chunks: TranslationChunk[]) {
  return sortChunks(chunks)
    .map((chunk) => chunk.translated_text?.trim() ?? "")
    .filter(Boolean)
    .join("\n\n")
}

export function formatSourceAndTranslation(chunks: TranslationChunk[]) {
  return sortChunks(chunks)
    .map((chunk) =>
      [
        `[${chunk.index + 1}]`,
        "원문:",
        chunk.source_text,
        "",
        "번역:",
        chunk.translated_text ?? "",
      ].join("\n"),
    )
    .join("\n\n")
}

export function normalizeSourceLang(value: string): SourceLang {
  if (value === "auto" || value === "ja" || value === "zh-CN" || value === "zh-TW" || value === "en") {
    return value
  }
  return "ja"
}
