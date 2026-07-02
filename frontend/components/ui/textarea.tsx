import * as React from "react"
import { cn } from "@/lib/utils"

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-40 w-full resize-y rounded-lg border border-[#d9d9dd] bg-white px-3 py-2 text-sm leading-6 text-[#212121] placeholder:text-[#93939f] focus:border-[#9b60aa]",
        className,
      )}
      {...props}
    />
  ),
)

Textarea.displayName = "Textarea"
