import { render, screen, within } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { ParallelTranslationView } from "@/components/parallel-translation-view"
import type { TranslationChunk } from "@/lib/types"

const chunks: TranslationChunk[] = [
  {
    index: 1,
    source_text: "後の原文",
    translated_text: "뒤 번역",
    status: "completed",
  },
  {
    index: 0,
    source_text: "先の原文",
    translated_text: "앞 번역",
    status: "completed",
  },
]

describe("ParallelTranslationView", () => {
  it("renders parallel chunks in index order with source and translation panes", () => {
    render(<ParallelTranslationView chunks={chunks} viewMode="parallel" />)

    const articles = screen.getAllByRole("article")
    expect(within(articles[0]).getByText("先の原文")).toBeInTheDocument()
    expect(within(articles[0]).getByText("앞 번역")).toBeInTheDocument()
    expect(within(articles[1]).getByText("後の原文")).toBeInTheDocument()
    expect(within(articles[1]).getByText("뒤 번역")).toBeInTheDocument()
  })

  it("renders translation-only mode as a single reader in index order", () => {
    render(<ParallelTranslationView chunks={chunks} viewMode="translation_only" />)

    const reader = screen.getByRole("article", { name: "번역문" })
    const readerChunks = within(reader).getAllByTestId("reader-chunk")

    expect(readerChunks).toHaveLength(2)
    expect(readerChunks[0]).toHaveTextContent("앞 번역")
    expect(readerChunks[1]).toHaveTextContent("뒤 번역")
    expect(screen.queryByText("先の原文")).not.toBeInTheDocument()
  })

  it("renders failed chunk message in parallel mode", () => {
    render(
      <ParallelTranslationView
        viewMode="parallel"
        chunks={[
          {
            index: 0,
            source_text: "原文",
            translated_text: null,
            status: "failed",
            error_message: "실패 이유",
          },
        ]}
      />,
    )

    expect(screen.getByText("번역 실패")).toBeInTheDocument()
    expect(screen.getByText("실패 이유")).toBeInTheDocument()
  })

  it("renders failed chunk message in translation-only reader", () => {
    render(
      <ParallelTranslationView
        viewMode="translation_only"
        chunks={[
          {
            index: 0,
            source_text: "原文",
            translated_text: null,
            status: "failed",
            error_message: "실패 이유",
          },
        ]}
      />,
    )

    const reader = screen.getByRole("article", { name: "번역문" })
    expect(within(reader).getByText("번역 실패")).toBeInTheDocument()
    expect(within(reader).getByText("실패 이유")).toBeInTheDocument()
  })
})
