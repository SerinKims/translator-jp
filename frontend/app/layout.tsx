import type { Metadata } from "next"
import "./globals.css"
import { QueryProvider } from "@/components/query-provider"

export const metadata: Metadata = {
  title: "translator-jp",
  description: "로컬 Ollama 기반 웹소설 번역 도구",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
