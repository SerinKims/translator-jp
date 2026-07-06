"use client";

import { FolderOpen, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getTranslationJob } from "@/lib/api/translationApi";
import type { TranslationHistoryItem } from "@/types/history";
import type { TranslationJob } from "@/types/translation";

export function TranslationHistory({
  clearHistory,
  deleteHistory,
  histories,
  onOpenHistory,
}: {
  clearHistory: () => void;
  deleteHistory: (id: string) => void;
  histories: TranslationHistoryItem[];
  onOpenHistory: (job: TranslationJob) => void;
}) {
  const [deleteTarget, setDeleteTarget] = useState<TranslationHistoryItem | null>(null);
  const [isClearOpen, setIsClearOpen] = useState(false);
  const totalPages = histories.reduce((sum, item) => sum + item.pageCount, 0);
  const translatedPages = histories.reduce((sum, item) => sum + item.translatedCount, 0);

  const openHistory = (history: TranslationHistoryItem) => {
    const storedJob = getTranslationJob(history.jobId);
    if (storedJob) {
      onOpenHistory(storedJob);
    }
  };

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>번역 이력</CardTitle>
            <CardDescription className="mt-2">지금까지 실행한 번역 작업을 다시 열거나 삭제할 수 있습니다.</CardDescription>
          </div>
          <Button type="button" variant="destructive" onClick={() => setIsClearOpen(true)} disabled={histories.length === 0}>
            <Trash2 className="h-4 w-4" />
            전체 이력 삭제
          </Button>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <SummaryCard label="전체 번역 작업" value={histories.length} />
          <SummaryCard label="누적 page 수" value={totalPages} />
          <SummaryCard label="번역 완료 page" value={translatedPages} />
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {histories.length === 0 ? (
          <div className="rounded-lg border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">
            아직 번역 이력이 없습니다. 번역을 실행하면 이곳에 자동으로 저장됩니다.
          </div>
        ) : (
          histories.map((history) => (
            <article key={history.id} className="flex flex-col gap-4 rounded-lg border p-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0">
                <div className="truncate font-semibold">{history.title}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary">{history.inputMode === "url" ? "URL" : "텍스트"}</Badge>
                  <span>{formatDate(history.createdAt)}</span>
                  <span>{history.sourceLang} → {history.targetLang}</span>
                  <span>{history.model}</span>
                  <span>{history.translatedCount} / {history.pageCount} page</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="button" size="sm" onClick={() => openHistory(history)}>
                  <FolderOpen className="h-4 w-4" />
                  열기
                </Button>
                <Button type="button" size="sm" variant="destructive" onClick={() => setDeleteTarget(history)}>
                  <Trash2 className="h-4 w-4" />
                  삭제
                </Button>
              </div>
            </article>
          ))
        )}
      </CardContent>

      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>이 번역 이력을 삭제할까요?</AlertDialogTitle>
            <AlertDialogDescription>삭제한 mock 이력은 되돌릴 수 없습니다.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTarget) {
                  deleteHistory(deleteTarget.id);
                }
                setDeleteTarget(null);
              }}
            >
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={isClearOpen} onOpenChange={setIsClearOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>전체 이력을 삭제할까요?</AlertDialogTitle>
            <AlertDialogDescription>현재 저장된 모든 mock 번역 작업이 삭제됩니다.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                clearHistory();
                setIsClearOpen(false);
              }}
            >
              전체 삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-4">
      <div className="text-2xl font-bold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function formatDate(isoString: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoString));
}
