"use client";

import { RotateCcw, Save } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DEFAULT_MODEL_SETTINGS, type ModelSettings as ModelSettingsType } from "@/types/translation";

export function ModelSettings({
  settings,
  onSettingsChange,
}: {
  settings: ModelSettingsType;
  onSettingsChange: (settings: ModelSettingsType) => void;
}) {
  const [draft, setDraft] = useState(settings);
  const [isSavedOpen, setIsSavedOpen] = useState(false);

  const save = () => {
    onSettingsChange(draft);
    setIsSavedOpen(true);
  };

  const restore = () => {
    setDraft(DEFAULT_MODEL_SETTINGS);
    onSettingsChange(DEFAULT_MODEL_SETTINGS);
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card>
        <CardHeader>
          <CardTitle>모델 상세 설정</CardTitle>
          <CardDescription>기본 번역 옵션을 설정합니다. 번역 작업 화면의 옵션과 함께 API mock 요청에 반영됩니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <LabeledField label="기본 모델">
              <Select value={draft.defaultModel} onValueChange={(value) => setDraft((current) => ({ ...current, defaultModel: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gemma4:26b-a4b-it-q4_K_M">gemma4:26b-a4b-it-q4_K_M</SelectItem>
                  <SelectItem value="gemma4:12b">gemma4:12b</SelectItem>
                  <SelectItem value="qwen2.5:14b">qwen2.5:14b</SelectItem>
                </SelectContent>
              </Select>
            </LabeledField>
            <LabeledField label="Prompt Version">
              <Input value={draft.promptVersion} onChange={(event) => setDraft((current) => ({ ...current, promptVersion: event.target.value }))} />
            </LabeledField>
            <LabeledField label="Temperature">
              <Input type="number" step={0.1} value={draft.temperature} onChange={(event) => setDraft((current) => ({ ...current, temperature: Number(event.target.value) }))} />
            </LabeledField>
            <LabeledField label="Top P">
              <Input type="number" step={0.05} value={draft.topP} onChange={(event) => setDraft((current) => ({ ...current, topP: Number(event.target.value) }))} />
            </LabeledField>
            <LabeledField label="Context Window">
              <Input type="number" value={draft.contextWindow} onChange={(event) => setDraft((current) => ({ ...current, contextWindow: Number(event.target.value) }))} />
            </LabeledField>
            <LabeledField label="Max Tokens">
              <Input type="number" value={draft.maxTokens} onChange={(event) => setDraft((current) => ({ ...current, maxTokens: Number(event.target.value) }))} />
            </LabeledField>
          </div>

          <div className="flex gap-2">
            <Button type="button" onClick={save}>
              <Save className="h-4 w-4" />
              설정 저장
            </Button>
            <Button type="button" variant="outline" onClick={restore}>
              <RotateCcw className="h-4 w-4" />
              기본값 복원
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>권장 설정</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-7 text-muted-foreground">
          <strong className="text-foreground">일본어/중국어/영어 → 한국어 번역</strong>
          <br />
          Temperature는 0.2~0.4 권장.
          <br />
          고유명사 보존과 용어집 사용은 기본 ON 권장.
          <br />
          Cache는 같은 page 반복 번역 비용을 줄이기 위해 ON 권장.
        </CardContent>
      </Card>

      <Dialog open={isSavedOpen} onOpenChange={setIsSavedOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>설정 저장 완료</DialogTitle>
            <DialogDescription>다음 번역 요청부터 변경한 모델 설정이 mock API 요청에 반영됩니다.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" onClick={() => setIsSavedOpen(false)}>
              확인
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function LabeledField({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      <span>{label}</span>
      {children}
    </label>
  );
}
