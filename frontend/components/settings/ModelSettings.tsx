"use client";

import { RotateCcw, Save } from "lucide-react";
import { useEffect, useState } from "react";

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

export const MODEL_SETTINGS_STORAGE_KEY = "translator-model-settings-v1";
const MODEL_PRESETS = ["gemma4:26b-a4b-it-q4_K_M", "gemma4:12b", "qwen2.5:14b"] as const;

export function ModelSettings({
  settings,
  onSettingsChange,
}: {
  settings: ModelSettingsType;
  onSettingsChange: (settings: ModelSettingsType) => void;
}) {
  const [draft, setDraft] = useState(settings);
  const [isSavedOpen, setIsSavedOpen] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setDraft(settings), 0);
    return () => window.clearTimeout(timer);
  }, [settings]);

  const save = () => {
    const trimmedModel = draft.defaultModel.trim();
    if (!trimmedModel) {
      return;
    }

    const nextDraft = { ...draft, defaultModel: trimmedModel };
    setDraft(nextDraft);
    onSettingsChange(nextDraft);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(MODEL_SETTINGS_STORAGE_KEY, JSON.stringify(nextDraft));
    }
    setIsSavedOpen(true);
  };

  const restore = () => {
    setDraft(DEFAULT_MODEL_SETTINGS);
    onSettingsChange(DEFAULT_MODEL_SETTINGS);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(MODEL_SETTINGS_STORAGE_KEY, JSON.stringify(DEFAULT_MODEL_SETTINGS));
    }
  };

  const isModelNameInvalid = !draft.defaultModel.trim();

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card>
        <CardHeader>
          <CardTitle>모델 설정</CardTitle>
          <CardDescription>
            로컬 Ollama에 설치된 모델명을 직접 입력할 수 있고, Ollama 옵션은 로컬 설정으로 보관합니다. prompt version은 백엔드가 원문 언어에 따라 자동
            선택합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <LabeledField label="모델명">
              <Input
                aria-describedby={isModelNameInvalid ? "model-name-error" : undefined}
                aria-invalid={isModelNameInvalid}
                list="ollama-model-presets"
                placeholder="gemma4:26b-a4b-it-q4_K_M"
                value={draft.defaultModel}
                onChange={(event) => setDraft((current) => ({ ...current, defaultModel: event.target.value }))}
              />
              <datalist id="ollama-model-presets">
                {MODEL_PRESETS.map((model) => (
                  <option key={model} value={model} />
                ))}
              </datalist>
              {isModelNameInvalid && (
                <p id="model-name-error" className="text-xs font-normal text-destructive">
                  모델명을 입력해주세요.
                </p>
              )}
            </LabeledField>
            <LabeledField label="Style">
              <Select value={draft.style} onValueChange={(value) => setDraft((current) => ({ ...current, style: value as ModelSettingsType["style"] }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="webnovel">Webnovel</SelectItem>
                  <SelectItem value="lightnovel">Light novel</SelectItem>
                  <SelectItem value="literal">Literal</SelectItem>
                  <SelectItem value="natural">Natural</SelectItem>
                </SelectContent>
              </Select>
            </LabeledField>
            <LabeledField label="Honorific Policy">
              <Select
                value={draft.honorificPolicy}
                onValueChange={(value) => setDraft((current) => ({ ...current, honorificPolicy: value as ModelSettingsType["honorificPolicy"] }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="preserve">Preserve</SelectItem>
                  <SelectItem value="naturalize">Naturalize</SelectItem>
                  <SelectItem value="omit">Omit</SelectItem>
                </SelectContent>
              </Select>
            </LabeledField>
            <LabeledField label="Ollama Think">
              <Select value={thinkToValue(draft.think)} onValueChange={(value) => setDraft((current) => ({ ...current, think: valueToThink(value) }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Off</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="true">On</SelectItem>
                </SelectContent>
              </Select>
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
            <Button type="button" onClick={save} disabled={isModelNameInvalid}>
              <Save className="h-4 w-4" />
              저장
            </Button>
            <Button type="button" variant="outline" onClick={restore}>
              <RotateCcw className="h-4 w-4" />
              기본값
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>적용 방식</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-7 text-muted-foreground">
          <strong className="text-foreground">한국어 번역은 고정입니다.</strong>
          <br />
          temperature, top_p, context window, max tokens는 Ollama options로 전달합니다.
          <br />
          모델명은 로컬 Ollama에 설치된 이름을 입력하거나 추천값에서 고를 수 있으며, 번역 요청과 이력에 그대로 반영됩니다.
        </CardContent>
      </Card>

      <Dialog open={isSavedOpen} onOpenChange={setIsSavedOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>설정 저장 완료</DialogTitle>
            <DialogDescription>다음 번역 요청부터 변경한 로컬 설정이 반영됩니다.</DialogDescription>
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

function thinkToValue(value: string | boolean): string {
  return typeof value === "boolean" ? String(value) : value;
}

function valueToThink(value: string): string | boolean {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return value;
}
