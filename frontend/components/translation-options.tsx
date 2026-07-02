"use client"

import { Languages, Settings2 } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import type { SourceLang, TranslationOptions } from "@/lib/types"

const sourceLangOptions: Array<{ value: SourceLang; label: string }> = [
  { value: "auto", label: "자동 감지" },
  { value: "ja", label: "일본어" },
  { value: "zh-CN", label: "중국어 간체" },
  { value: "zh-TW", label: "중국어 번체" },
  { value: "en", label: "영어" },
]

const stylePresetOptions = [
  { value: "webnovel", label: "웹소설체" },
  { value: "literal", label: "직역 중심" },
  { value: "natural", label: "자연스러운 의역" },
]

const honorificPresetOptions = [
  { value: "preserve", label: "원문 관계 보존" },
  { value: "formal", label: "존댓말 우선" },
  { value: "casual", label: "반말 우선" },
]

type TranslationOptionsProps = {
  options: TranslationOptions
  onChange: (options: TranslationOptions) => void
  disabled?: boolean
}

export function TranslationOptionsPanel({
  options,
  onChange,
  disabled,
}: TranslationOptionsProps) {
  const update = (changes: Partial<TranslationOptions>) => {
    onChange({ ...options, ...changes })
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <label className="space-y-2">
          <span className="flex items-center gap-2 text-sm font-medium">
            <Languages aria-hidden className="h-4 w-4" />
            원문 언어
          </span>
          <Select
            value={options.source_lang}
            disabled={disabled}
            onChange={(event) =>
              update({ source_lang: event.target.value as SourceLang })
            }
          >
            {sourceLangOptions.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        </label>
        <div className="space-y-2">
          <span className="flex items-center gap-2 text-sm font-medium">
            <Languages aria-hidden className="h-4 w-4" />
            번역 결과 언어
          </span>
          <div className="flex min-h-11 items-center rounded-lg border border-[#d9d9dd] bg-[#f7f7f7] px-3 text-sm">
            한국어
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Settings2 aria-hidden className="h-4 w-4" />
          번역 옵션
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          <PresetTextOption
            label="번역 스타일"
            value={options.style}
            presets={stylePresetOptions}
            disabled={disabled}
            placeholder="예: webnovel, noir, light-novel"
            onChange={(style) => update({ style })}
          />
          <PresetTextOption
            label="존댓말/반말 정책"
            value={options.honorific_policy}
            presets={honorificPresetOptions}
            disabled={disabled}
            placeholder="예: preserve, formal, casual"
            onChange={(honorific_policy) => update({ honorific_policy })}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <CheckOption
            label="고유명사 보존"
            checked={options.preserve_names}
            disabled={disabled}
            onChange={(checked) => update({ preserve_names: checked })}
          />
          <CheckOption
            label="용어집 사용"
            checked={options.use_glossary}
            disabled={disabled}
            onChange={(checked) => update({ use_glossary: checked })}
          />
          <CheckOption
            label="캐시 사용"
            checked={options.use_cache}
            disabled={disabled}
            onChange={(checked) => update({ use_cache: checked })}
          />
        </div>
      </div>
    </section>
  )
}

function PresetTextOption({
  label,
  value,
  presets,
  disabled,
  placeholder,
  onChange,
}: {
  label: string
  value: string
  presets: Array<{ value: string; label: string }>
  disabled?: boolean
  placeholder: string
  onChange: (value: string) => void
}) {
  const presetValues = new Set(presets.map((preset) => preset.value))
  const selectValue = presetValues.has(value) ? value : "__custom__"

  return (
    <div className="space-y-2 rounded-lg border border-[#d9d9dd] bg-white p-3">
      <label className="block space-y-2">
        <span className="text-sm font-medium">{label}</span>
        <Select
          value={selectValue}
          disabled={disabled}
          aria-label={`${label} 프리셋`}
          onChange={(event) => {
            if (event.target.value === "__custom__") {
              onChange("")
              return
            }
            onChange(event.target.value)
          }}
        >
          {presets.map((preset) => (
            <option key={preset.value} value={preset.value}>
              {preset.label}
            </option>
          ))}
          <option value="__custom__">직접 입력</option>
        </Select>
      </label>
      <label className="block space-y-2">
        <span className="text-xs text-[#75758a]">{label} 직접 입력</span>
        <Input
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          aria-label={`${label} 직접 입력`}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
    </div>
  )
}

function CheckOption({
  label,
  checked,
  disabled,
  onChange,
}: {
  label: string
  checked: boolean
  disabled?: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <label className="flex min-h-[58px] items-center gap-3 rounded-lg border border-[#d9d9dd] bg-white px-3 py-2 text-sm">
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        className="h-4 w-4 accent-[#17171c]"
        onChange={(event) => onChange(event.target.checked)}
      />
      {label}
    </label>
  )
}
