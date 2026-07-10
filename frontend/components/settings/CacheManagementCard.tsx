"use client";

import { Trash2 } from "lucide-react";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api/client";

export function CacheManagementCard({
  clearCache,
  error,
  isClearing,
  isSuccess,
}: {
  clearCache: () => void;
  error: unknown;
  isClearing: boolean;
  isSuccess: boolean;
}) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle>캐시 관리</CardTitle>
          <CardDescription className="mt-2">
            서버에 저장된 번역 재사용 캐시만 삭제합니다. 번역 이력과 로컬 모델 설정은 유지됩니다.
          </CardDescription>
        </div>
        <Button
          type="button"
          variant="destructive"
          size="sm"
          disabled={isClearing}
          onClick={() => setIsConfirmOpen(true)}
        >
          <Trash2 className="h-4 w-4" />
          캐시 삭제
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {isSuccess ? (
          <div className="rounded-md border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-800">
            번역 캐시를 삭제했습니다. 다음 번역부터 새로 생성된 결과가 저장됩니다.
          </div>
        ) : null}
        {error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {getErrorMessage(error)}
          </div>
        ) : null}
      </CardContent>

      <AlertDialog open={isConfirmOpen} onOpenChange={setIsConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>번역 캐시를 삭제할까요?</AlertDialogTitle>
            <AlertDialogDescription>
              저장된 번역 캐시가 모두 삭제됩니다. 기존 번역 이력, page/chunk 기록, 피드백, 용어집은 삭제되지 않습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isClearing}>취소</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isClearing}
              onClick={() => {
                clearCache();
                setIsConfirmOpen(false);
              }}
            >
              {isClearing ? "삭제 중" : "캐시 삭제"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
