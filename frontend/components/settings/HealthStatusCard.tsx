"use client";

import { RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { HealthResponse } from "@/types/health";

export function HealthStatusCard({
  error,
  health,
  isFetching,
  onRefresh,
}: {
  error: unknown;
  health: HealthResponse | undefined;
  isFetching: boolean;
  onRefresh: () => void;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle>시스템 상태</CardTitle>
          <CardDescription className="mt-2">Backend와 로컬 번역 환경의 연결 상태를 확인합니다.</CardDescription>
        </div>
        <Button type="button" variant="outline" size="sm" disabled={isFetching} onClick={onRefresh}>
          <RefreshCw className={isFetching ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          {isFetching ? "확인 중" : "상태 새로고침"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            Backend에 연결할 수 없습니다.
          </div>
        ) : (
          <>
            <StatusRow label="Backend 연결" value={health ? "ok" : "checking"} />
            <StatusRow label="Ollama" value={health?.ollama ?? "checking"} />
            <StatusRow label="Database" value={health?.database ?? "checking"} />
            <StatusRow
              label="Model"
              value={health && health.ollama !== "ok" ? "unavailable" : health?.model ?? "checking"}
              model
            />
            {health?.message ? (
              <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
                {health.message}
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function StatusRow({ label, model = false, value }: { label: string; model?: boolean; value: string }) {
  const ok = model
    ? value !== "not_found" && value !== "checking" && value !== "unavailable"
    : value === "ok";
  const checking = value === "checking";
  const text = statusText({ checking, model, ok, value });
  return (
    <div className="flex items-center justify-between gap-4 rounded-md border px-3 py-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <Badge variant={checking ? "secondary" : ok ? "success" : "destructive"}>
        {text}
      </Badge>
    </div>
  );
}

function statusText({
  checking,
  model,
  ok,
  value,
}: {
  checking: boolean;
  model: boolean;
  ok: boolean;
  value: string;
}) {
  if (checking) return "확인 중";
  if (model && ok) return value;
  if (ok) return "정상";
  if (model && value === "unavailable") return "확인 불가";
  if (model) return "모델 없음";
  return "오류";
}
