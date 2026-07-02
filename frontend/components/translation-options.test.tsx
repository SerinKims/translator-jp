import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { TranslationOptionsPanel } from "@/components/translation-options"
import type { TranslationOptions } from "@/lib/types"

const options: TranslationOptions = {
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

describe("TranslationOptionsPanel", () => {
  it("updates style from a preset", () => {
    const onChange = vi.fn()
    render(<TranslationOptionsPanel options={options} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText("번역 스타일 프리셋"), {
      target: { value: "literal" },
    })

    expect(onChange).toHaveBeenCalledWith({
      ...options,
      style: "literal",
    })
  })

  it("updates honorific policy from direct input", () => {
    const onChange = vi.fn()
    render(<TranslationOptionsPanel options={options} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText("존댓말/반말 정책 직접 입력"), {
      target: { value: "formal-in-dialogue" },
    })

    expect(onChange).toHaveBeenCalledWith({
      ...options,
      honorific_policy: "formal-in-dialogue",
    })
  })

  it("toggles glossary usage", () => {
    const onChange = vi.fn()
    render(<TranslationOptionsPanel options={options} onChange={onChange} />)

    fireEvent.click(screen.getByLabelText("용어집 사용"))

    expect(onChange).toHaveBeenCalledWith({
      ...options,
      use_glossary: false,
    })
  })
})
