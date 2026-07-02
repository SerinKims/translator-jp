"use client"

import { Columns2, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { ViewMode } from "@/lib/types"

type ViewModeToggleProps = {
  value: ViewMode
  onChange: (value: ViewMode) => void
}

export function ViewModeToggle({ value, onChange }: ViewModeToggleProps) {
  return (
    <div className="inline-flex rounded-full border border-[#d9d9dd] bg-white p-1">
      <Button
        aria-pressed={value === "parallel"}
        variant={value === "parallel" ? "primary" : "ghost"}
        className="min-h-8 px-3"
        onClick={() => onChange("parallel")}
      >
        <Columns2 aria-hidden className="h-4 w-4" />
        원문+번역
      </Button>
      <Button
        aria-pressed={value === "translation_only"}
        variant={value === "translation_only" ? "primary" : "ghost"}
        className="min-h-8 px-3"
        onClick={() => onChange("translation_only")}
      >
        <FileText aria-hidden className="h-4 w-4" />
        번역만
      </Button>
    </div>
  )
}
