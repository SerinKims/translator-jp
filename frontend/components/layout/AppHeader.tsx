"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { AppSection } from "@/components/layout/AppSidebar";
import type { InputMode } from "@/types/translation";

const sectionText: Record<AppSection, { title: string; desc: string }> = {
  translate: {
    title: "번역 작업",
    desc: "URL 또는 텍스트를 입력하고 API의 page 단위 번역 흐름으로 첫 page부터 번역합니다.",
  },
  viewer: {
    title: "번역본 보기",
    desc: "API 응답의 page 상태를 기준으로 원문과 번역본을 확인합니다.",
  },
  history: {
    title: "번역 이력",
    desc: "지금까지 실행한 번역 작업을 다시 열거나 삭제합니다.",
  },
  glossary: {
    title: "용어집",
    desc: "고유명사와 반복 용어를 추가, 수정, 삭제합니다.",
  },
  settings: {
    title: "모델 설정",
    desc: "번역 모델, prompt version, token 설정을 관리합니다.",
  },
};

export function AppHeader({
  activeSection,
  inputMode,
  pageCount,
  currentPageIndex,
  progress,
  statusLabel,
}: {
  activeSection: AppSection;
  inputMode: InputMode;
  pageCount: number;
  currentPageIndex: number;
  progress: number;
  statusLabel: string;
}) {
  const text = sectionText[activeSection];
  const done = statusLabel.includes("완료");
  const pending = statusLabel.includes("대기");

  return (
    <header className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
      <div>
        <h1 className="text-3xl font-bold tracking-normal">{text.title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{text.desc}</p>
      </div>

      <Card className="w-full shadow-sm xl:w-80">
        <CardContent className="p-4">
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">입력 방식</span>
              <strong>{inputMode === "url" ? "URL" : "텍스트"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">페이지</span>
              <strong>{pageCount > 0 ? `${currentPageIndex + 1} / ${pageCount}` : "0 / 0"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">번역 상태</span>
              <Badge variant={done ? "success" : pending ? "warning" : "secondary"}>{statusLabel}</Badge>
            </div>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          </div>
        </CardContent>
      </Card>
    </header>
  );
}
