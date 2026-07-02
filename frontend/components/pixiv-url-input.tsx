"use client"

import { Link } from "lucide-react"
import { Input } from "@/components/ui/input"

type PixivUrlInputProps = {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function PixivUrlInput({ value, onChange, disabled }: PixivUrlInputProps) {
  return (
    <label className="block space-y-2">
      <span className="flex items-center gap-2 text-sm font-medium text-[#212121]">
        <Link aria-hidden className="h-4 w-4" />
        pixiv URL
      </span>
      <Input
        value={value}
        disabled={disabled}
        inputMode="url"
        placeholder="https://www.pixiv.net/novel/show.php?id=12345678"
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  )
}
