import type { Metadata } from "next";
import "./globals.css";

import { QueryProvider } from "@/components/providers/QueryProvider";

export const metadata: Metadata = {
  title: "Novel Translator",
  description: "URL and pasted text translator UI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
