import * as React from "react"
import { cn } from "@/lib/utils"

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger"

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

const variants: Record<ButtonVariant, string> = {
  primary: "bg-[#17171c] text-white hover:bg-black disabled:bg-[#93939f]",
  secondary: "bg-white text-[#17171c] hover:bg-[#f7f7f7]",
  outline:
    "border border-[#d9d9dd] bg-white text-[#17171c] hover:border-[#17171c]",
  ghost: "bg-transparent text-[#17171c] hover:bg-[#f7f7f7]",
  danger: "bg-[#b30000] text-white hover:bg-[#8f0000]",
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-full px-5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-70",
        variants[variant],
        className,
      )}
      {...props}
    />
  ),
)

Button.displayName = "Button"
