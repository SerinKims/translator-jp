import { describe, expect, it } from "vitest"
import {
  chooseTranslationRoute,
  formatSourceAndTranslation,
  formatTranslationOnly,
  nextPageIndex,
  previousPageIndex,
  sortChunks,
  toPageTranslateRequest,
} from "@/lib/translation-utils"
import type { TranslationChunk, TranslationOptions } from "@/lib/types"

const chunks: TranslationChunk[] = [
  {
    index: 2,
    source_text: "third source",
    translated_text: "third translation",
    status: "completed",
  },
  {
    index: 0,
    source_text: "first source",
    translated_text: "first translation",
    status: "completed",
  },
]

const options: TranslationOptions = {
  source_lang: "ja",
  target_lang: "ko",
  translate_scope: "first_page",
  page_index: 0,
  style: "noir-webnovel",
  honorific_policy: "formal-for-narration",
  preserve_names: true,
  use_glossary: false,
  use_cache: true,
  stream: false,
}

describe("translation utils", () => {
  it("prefers pixiv URL when both inputs are present", () => {
    expect(chooseTranslationRoute("https://www.pixiv.net/novel/show.php?id=1", "text")).toBe(
      "pixiv",
    )
  })

  it("returns empty route for blank inputs", () => {
    expect(chooseTranslationRoute(" ", "\n")).toBe("empty")
  })

  it("sorts chunks by index", () => {
    expect(sortChunks(chunks).map((chunk) => chunk.index)).toEqual([0, 2])
  })

  it("formats translation-only copy text", () => {
    expect(formatTranslationOnly(chunks)).toBe(
      "first translation\n\nthird translation",
    )
  })

  it("formats source and translation copy text", () => {
    expect(formatSourceAndTranslation(chunks)).toContain("[1]\n원문:\nfirst source")
    expect(formatSourceAndTranslation(chunks)).toContain(
      "번역:\nthird translation",
    )
  })

  it("calculates page indexes", () => {
    expect(nextPageIndex(0)).toBe(1)
    expect(previousPageIndex(2)).toBe(1)
    expect(previousPageIndex(0)).toBe(0)
  })

  it("preserves current translation options in page translate requests", () => {
    expect(toPageTranslateRequest(options, "en", "ko")).toMatchObject({
      source_lang: "en",
      target_lang: "ko",
      translate_scope: "current_page",
      style: "noir-webnovel",
      honorific_policy: "formal-for-narration",
      preserve_names: true,
      use_glossary: false,
      use_cache: true,
      stream: false,
      force: false,
    })
  })
})
