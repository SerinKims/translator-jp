"use client";

import { BookOpenText, Clipboard, Languages } from "lucide-react";
import { useState } from "react";

import { PageNavigator } from "@/components/translator/PageNavigator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { createPageTranslateRequest, createTranslationRequest, createUrlTranslationRequest } from "@/lib/translationRequests";
import type { TranslationJob, TranslationRequest, UrlTranslationRequest, ViewerMode } from "@/types/translation";

export function TranslationViewer({
  currentJob,
  currentPageIndex,
  isTranslating,
  onPageChange,
  onTranslateAllText,
  onTranslateAllUrl,
  onTranslateCurrent,
  setViewerMode,
  viewerMode,
}: {
  currentJob: TranslationJob | null;
  currentPageIndex: number;
  isTranslating: boolean;
  onPageChange: (index: number) => void;
  onTranslateAllText: (request: TranslationRequest) => void;
  onTranslateAllUrl: (request: UrlTranslationRequest) => void;
  onTranslateCurrent: ReturnType<typeof createPageTranslateRequest> extends infer T ? (request: T) => void : never;
  setViewerMode: (mode: ViewerMode) => void;
  viewerMode: ViewerMode;
}) {
  const [copyLabel, setCopyLabel] = useState("복사");
  const activePage = currentJob?.pages[currentPageIndex] ?? null;
  const pageCount = currentJob?.pages.length ?? 0;

  const copyTranslation = async () => {
    if (!activePage?.translatedText) {
      setCopyLabel("결과 없음");
      window.setTimeout(() => setCopyLabel("복사"), 1200);
      return;
    }

    await navigator.clipboard.writeText(activePage.translatedText);
    setCopyLabel("복사 완료");
    window.setTimeout(() => setCopyLabel("복사"), 1200);
  };

  const translateAll = () => {
    if (!currentJob) {
      return;
    }

    const text = currentJob.pages.map((page) => page.sourceText).join("\n\n[newpage]\n\n");
    if (currentJob.inputMode === "url") {
      onTranslateAllUrl(
        createUrlTranslationRequest({
          url: currentJob.sourceUrl ?? "",
          sourceLang: currentJob.sourceLang,
          options: currentJob.options,
          viewerMode,
        }),
      );
    } else {
      onTranslateAllText(
        createTranslationRequest({
          text,
          sourceLang: currentJob.sourceLang,
          options: currentJob.options,
        }),
      );
    }
  };

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <CardTitle>번역본 보기</CardTitle>
            <CardDescription className="mt-2">API 응답의 page 상태를 기준으로 원문과 번역본을 이동하며 확인합니다.</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => currentJob && onTranslateCurrent(createPageTranslateRequest(currentJob))} disabled={!currentJob || isTranslating}>
              <Languages className="h-4 w-4" />
              현재 page 번역
            </Button>
            <Button type="button" variant="success" onClick={translateAll} disabled={!currentJob || isTranslating}>
              <BookOpenText className="h-4 w-4" />
              전체 번역
            </Button>
          </div>
        </div>
        <Separator />
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <PageNavigator currentPageIndex={currentPageIndex} onPageChange={onPageChange} pageCount={pageCount} />
          <div className="w-full xl:w-56">
            <Select value={viewerMode} onValueChange={(value) => setViewerMode(value as ViewerMode)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="translation">번역본만 보기</SelectItem>
                <SelectItem value="both">원문 + 번역본 보기</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {!currentJob ? (
          <EmptyViewer />
        ) : (
          <div className={viewerMode === "both" ? "grid gap-4 xl:grid-cols-2" : "grid gap-4"}>
            {viewerMode === "both" && (
              <ViewerPanel title="원문" meta={`page ${currentPageIndex + 1} / ${pageCount}`}>
                {activePage?.sourceText || "아직 원문이 없습니다."}
              </ViewerPanel>
            )}
            <ViewerPanel
              title="한국어 번역본"
              meta={<Badge variant={activePage?.status === "completed" ? "success" : "secondary"}>{activePage?.status === "completed" ? "완료" : "대기"}</Badge>}
              action={
                <Button type="button" variant="outline" size="sm" onClick={copyTranslation}>
                  <Clipboard className="h-4 w-4" />
                  {copyLabel}
                </Button>
              }
            >
              {activePage?.translatedText || "아직 이 page의 번역 결과가 없습니다. 현재 page 번역 또는 전체 번역을 실행하세요."}
            </ViewerPanel>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ViewerPanel({
  action,
  children,
  meta,
  title,
}: {
  action?: React.ReactNode;
  children: React.ReactNode;
  meta: React.ReactNode;
  title: string;
}) {
  return (
    <article className="flex min-h-96 flex-col overflow-hidden rounded-lg border bg-white">
      <header className="flex min-h-12 items-center justify-between gap-3 border-b bg-muted/50 px-4 py-3 text-sm font-semibold">
        <div className="flex items-center gap-2">
          <span>{title}</span>
          <span className="text-xs font-normal text-muted-foreground">{meta}</span>
        </div>
        {action}
      </header>
      <div className="whitespace-pre-wrap p-4 text-sm leading-7">{children}</div>
    </article>
  );
}

function EmptyViewer() {
  return (
    <div className="grid min-h-80 place-items-center rounded-lg border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">
      아직 원문이 없습니다. 번역 작업 화면에서 URL 또는 텍스트를 입력하세요.
    </div>
  );
}
