"use client"

import { FileText } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

type SourceTextInputProps = {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function SourceTextInput({ value, onChange, disabled }: SourceTextInputProps) {
  return (
    <label className="block space-y-2">
      <span className="flex items-center gap-2 text-sm font-medium text-[#212121]">
        <FileText aria-hidden className="h-4 w-4" />
        직접 입력
      </span>
      <Textarea
        value={value}
        disabled={disabled}
        placeholder="번역할 원문을 붙여넣으세요. [newpage]가 있으면 첫 페이지만 먼저 번역합니다."
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  )
}
