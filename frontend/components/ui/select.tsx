import * as React from "react"
import { cn } from "@/lib/utils"

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "min-h-11 w-full rounded-lg border border-[#d9d9dd] bg-white px-3 py-2 text-sm text-[#212121] focus:border-[#9b60aa]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
)

Select.displayName = "Select"
