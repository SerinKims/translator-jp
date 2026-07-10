"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { AppSection } from "@/components/layout/AppSidebar";
import type { InputMode } from "@/types/translation";
import type { HealthState } from "@/types/health";

const sectionText: Record<AppSection, { title: string; desc: string }> = {
  translate: {
    title: "번역 작업",
    desc: "URL 원문을 가져오거나 텍스트를 붙여넣고 page 단위로 번역합니다.",
  },
  viewer: {
    title: "번역본 보기",
    desc: "원문과 번역본을 page 단위로 확인하고 복사합니다.",
  },
  history: {
    title: "번역 이력",
    desc: "백엔드에 저장된 과거 번역 작업을 다시 엽니다.",
  },
  glossary: {
    title: "용어집",
    desc: "고유명사와 반복 용어를 관리합니다.",
  },
  settings: {
    title: "모델 설정",
    desc: "번역 옵션과 로컬 선호 설정을 관리합니다.",
  },
};

export function AppHeader({
  activeSection,
  inputMode,
  healthState,
  onOpenHealthDetails,
  pageCount,
  currentPageIndex,
  progress,
  statusLabel,
}: {
  activeSection: AppSection;
  inputMode: InputMode;
  healthState: HealthState;
  onOpenHealthDetails: () => void;
  pageCount: number;
  currentPageIndex: number;
  progress: number;
  statusLabel: string;
}) {
  const text = sectionText[activeSection];
  const done = statusLabel.includes("완료");
  const pending = statusLabel.includes("대기") || statusLabel.includes("준비");

  return (
    <header className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
      <div>
        <h1 className="text-3xl font-bold tracking-normal">{text.title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{text.desc}</p>
        <button type="button" className="mt-3" onClick={onOpenHealthDetails}>
          <Badge variant={healthBadgeVariant(healthState)}>{healthLabel(healthState)}</Badge>
        </button>
      </div>

      <Card className="w-full shadow-sm xl:w-80">
        <CardContent className="p-4">
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">입력 방식</span>
              <strong>{inputMode === "url" ? "URL" : "텍스트"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">page</span>
              <strong>{pageCount > 0 ? `${currentPageIndex + 1} / ${pageCount}` : "0 / 0"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">상태</span>
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

function healthLabel(state: HealthState): string {
  if (state === "healthy") return "시스템 정상";
  if (state === "degraded") return "시스템 점검 필요";
  if (state === "unreachable") return "Backend 연결 실패";
  return "시스템 확인 중";
}

function healthBadgeVariant(state: HealthState): "success" | "warning" | "destructive" | "secondary" {
  if (state === "healthy") return "success";
  if (state === "degraded") return "warning";
  if (state === "unreachable") return "destructive";
  return "secondary";
}
