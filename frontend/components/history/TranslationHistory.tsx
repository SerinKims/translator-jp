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
import { getErrorMessage } from "@/lib/api/client";
import type { TranslationHistoryItem } from "@/types/history";

export function TranslationHistory({
  clearHistory,
  deleteHistory,
  histories,
  isLoading,
  isMutating,
  onOpenHistory,
}: {
  clearHistory: () => void;
  deleteHistory: (id: string) => void;
  histories: TranslationHistoryItem[];
  isLoading: boolean;
  isMutating: boolean;
  onOpenHistory: (jobId: number) => void;
}) {
  const [deleteTarget, setDeleteTarget] = useState<TranslationHistoryItem | null>(null);
  const [isClearOpen, setIsClearOpen] = useState(false);
  const totalPages = histories.reduce((sum, item) => sum + item.pageCount, 0);
  const translatedPages = histories.reduce((sum, item) => sum + item.translatedCount, 0);

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>번역 이력</CardTitle>
            <CardDescription className="mt-2">백엔드에 저장된 번역 작업을 다시 열거나 영구 삭제할 수 있습니다.</CardDescription>
          </div>
          <Button type="button" variant="destructive" onClick={() => setIsClearOpen(true)} disabled={histories.length === 0 || isMutating}>
            <Trash2 className="h-4 w-4" />
            전체 삭제
          </Button>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <SummaryCard label="번역 작업" value={histories.length} />
          <SummaryCard label="전체 page" value={totalPages} />
          <SummaryCard label="완료 chunk" value={translatedPages} />
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {isLoading ? (
          <EmptyState>번역 이력을 불러오는 중입니다.</EmptyState>
        ) : histories.length === 0 ? (
          <EmptyState>아직 번역 이력이 없습니다.</EmptyState>
        ) : (
          histories.map((history) => (
            <article key={history.id} className="flex flex-col gap-4 rounded-md border p-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0">
                <div className="truncate font-semibold">{history.title}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary">{history.inputMode === "url" ? "URL" : "텍스트"}</Badge>
                  <Badge variant={history.status === "failed" ? "destructive" : history.status === "completed" ? "success" : "secondary"}>{statusLabel(history.status)}</Badge>
                  {history.sourceAuthor && <span>작가: {history.sourceAuthor}</span>}
                  <span>{formatDate(history.createdAt)}</span>
                  <span>{history.sourceLang} → {history.targetLang}</span>
                  <span>{history.model}</span>
                  <span>{history.translatedCount} / {history.pageCount} chunk</span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{history.sourcePreview}</p>
              </div>
              <div className="flex gap-2">
                <Button type="button" size="sm" onClick={() => onOpenHistory(history.jobId)} disabled={isMutating}>
                  <FolderOpen className="h-4 w-4" />
                  열기
                </Button>
                <Button type="button" size="sm" variant="outline" onClick={() => setDeleteTarget(history)} disabled={isMutating}>
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
            <AlertDialogTitle>이 이력을 삭제할까요?</AlertDialogTitle>
            <AlertDialogDescription>서버에 저장된 원문, 번역문, page, chunk 이력이 영구 삭제됩니다.</AlertDialogDescription>
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
            <AlertDialogDescription>서버에 저장된 모든 번역 이력이 영구 삭제됩니다. 번역 캐시는 유지됩니다.</AlertDialogDescription>
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

export function HistoryError({ error }: { error: unknown }) {
  return <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{getErrorMessage(error)}</div>;
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border bg-muted/30 p-4">
      <div className="text-2xl font-bold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return <div className="rounded-md border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">{children}</div>;
}

function statusLabel(status: string): string {
  if (status === "completed") {
    return "완료";
  }
  if (status === "failed") {
    return "실패";
  }
  if (status === "translating") {
    return "처리 중";
  }
  return "대기";
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
