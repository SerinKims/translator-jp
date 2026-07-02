import * as React from "react"
import { cn } from "@/lib/utils"

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "min-h-11 w-full rounded-lg border border-[#d9d9dd] bg-white px-3 py-2 text-sm text-[#212121] placeholder:text-[#93939f] focus:border-[#9b60aa]",
        className,
      )}
      {...props}
    />
  ),
)

Input.displayName = "Input"
