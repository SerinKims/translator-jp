"use client";

import { BookOpenText, Clock3, Languages } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { createOptionsFromSettings, createTranslationRequest, createUrlTranslationRequest } from "@/lib/translationRequests";
import type { AppSection } from "@/components/layout/AppSidebar";
import type { InputMode, ModelSettings, SourceLanguage, TranslationOptions, TranslationRequest, UrlTranslationRequest, ViewerMode } from "@/types/translation";

const sampleText = `第一ページです。
少年は夕焼けの空を見上げた。
風が静かに頬を撫でていく。

[newpage]

第二ページです。
彼は小さく息を吐いて、もう一度だけ前を見た。`;

export function TranslatePanel({
  isTranslating,
  modelSettings,
  onInputModeChange,
  onSectionChange,
  onTranslateTextAll,
  onTranslateTextFirst,
  onTranslateUrlAll,
  onTranslateUrlFirst,
}: {
  isTranslating: boolean;
  modelSettings: ModelSettings;
  onInputModeChange: (mode: InputMode) => void;
  onSectionChange: (section: AppSection) => void;
  onTranslateTextAll: (request: TranslationRequest) => void;
  onTranslateTextFirst: (request: TranslationRequest) => void;
  onTranslateUrlAll: (request: UrlTranslationRequest) => void;
  onTranslateUrlFirst: (request: UrlTranslationRequest) => void;
}) {
  const [inputMode, setInputMode] = useState<InputMode>("url");
  const [sourceUrl, setSourceUrl] = useState("https://example.com/novel/sample");
  const [sourceText, setSourceText] = useState(sampleText);
  const [sourceLang, setSourceLang] = useState<SourceLanguage>("ja");
  const [viewerMode, setViewerMode] = useState<ViewerMode>("both");
  const [options, setOptions] = useState<TranslationOptions>(() => createOptionsFromSettings(modelSettings));

  const updateMode = (mode: InputMode) => {
    setInputMode(mode);
    onInputModeChange(mode);
  };

  const buildOptions = () =>
    createOptionsFromSettings(modelSettings, {
      ...options,
      model: options.model,
      promptVersion: modelSettings.promptVersion,
      topP: modelSettings.topP,
      contextWindow: modelSettings.contextWindow,
      maxTokens: modelSettings.maxTokens,
    });

  const runFirst = () => {
    const mergedOptions = buildOptions();
    if (inputMode === "url") {
      onTranslateUrlFirst(
        createUrlTranslationRequest({
          url: sourceUrl,
          sourceLang,
          options: mergedOptions,
          viewerMode,
        }),
      );
    } else {
      onTranslateTextFirst(
        createTranslationRequest({
          text: sourceText,
          sourceLang,
          options: mergedOptions,
        }),
      );
    }
    onSectionChange("viewer");
  };

  const runAll = () => {
    const mergedOptions = buildOptions();
    if (inputMode === "url") {
      onTranslateUrlAll(
        createUrlTranslationRequest({
          url: sourceUrl,
          sourceLang,
          options: mergedOptions,
          viewerMode,
        }),
      );
    } else {
      onTranslateTextAll(
        createTranslationRequest({
          text: sourceText,
          sourceLang,
          options: mergedOptions,
        }),
      );
    }
    onSectionChange("viewer");
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card>
        <CardHeader>
          <CardTitle>원문 입력</CardTitle>
          <CardDescription>URL 또는 직접 붙여넣은 원문을 API mock adapter로 전달합니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <Tabs value={inputMode} onValueChange={(value) => updateMode(value as InputMode)}>
            <TabsList>
              <TabsTrigger value="url">URL 붙여넣기</TabsTrigger>
              <TabsTrigger value="text">텍스트 붙여넣기</TabsTrigger>
            </TabsList>

            <TabsContent value="url" className="space-y-4">
              <LabeledField label="소설 URL">
                <Input value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://example.com/novel/12345" />
              </LabeledField>
              <LabeledField label="URL 번역본 보기 방식">
                <Select value={viewerMode} onValueChange={(value) => setViewerMode(value as ViewerMode)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="translation">번역본만 보기</SelectItem>
                    <SelectItem value="both">원문 + 번역본 보기</SelectItem>
                  </SelectContent>
                </Select>
              </LabeledField>
            </TabsContent>

            <TabsContent value="text">
              <LabeledField label="원문 텍스트">
                <Textarea
                  value={sourceText}
                  onChange={(event) => setSourceText(event.target.value)}
                  className="min-h-72 font-mono leading-7"
                  placeholder="원문을 붙여넣으세요."
                />
              </LabeledField>
            </TabsContent>
          </Tabs>

          <div className="grid gap-4 md:grid-cols-2">
            <LabeledField label="원문 언어">
              <Select value={sourceLang} onValueChange={(value) => setSourceLang(value as SourceLanguage)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ja">일본어</SelectItem>
                  <SelectItem value="zh-TW">중국어 번체</SelectItem>
                  <SelectItem value="zh-CN">중국어 간체</SelectItem>
                  <SelectItem value="en">영어</SelectItem>
                </SelectContent>
              </Select>
            </LabeledField>
            <LabeledField label="번역 언어">
              <Select value="ko" disabled>
                <SelectTrigger>
                  <SelectValue placeholder="한국어 고정" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ko">한국어 고정</SelectItem>
                </SelectContent>
              </Select>
            </LabeledField>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={runFirst} disabled={isTranslating}>
              <Languages className="h-4 w-4" />
              번역하기
            </Button>
            <Button type="button" variant="success" onClick={runAll} disabled={isTranslating}>
              <BookOpenText className="h-4 w-4" />
              전체 번역
            </Button>
            <Button type="button" variant="outline" onClick={() => onSectionChange("viewer")}>
              번역본 보기
            </Button>
            <Button type="button" variant="outline" onClick={() => onSectionChange("history")}>
              <Clock3 className="h-4 w-4" />
              번역 이력
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>번역 옵션</CardTitle>
          <CardDescription>현재 옵션은 mock API 요청과 이력에 함께 저장됩니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <SwitchRow
            label="용어집 사용"
            help="등록된 고유명사/용어를 우선 적용합니다."
            checked={options.useGlossary}
            onCheckedChange={(checked) => setOptions((current) => ({ ...current, useGlossary: checked }))}
          />
          <SwitchRow
            label="Cache 사용"
            help="같은 원문은 기존 번역 결과를 재사용합니다."
            checked={options.useCache}
            onCheckedChange={(checked) => setOptions((current) => ({ ...current, useCache: checked }))}
          />
          <SwitchRow
            label="고유명사 보존"
            help="인명, 지명, 기술명 번역 흔들림을 줄입니다."
            checked={options.preserveNames}
            onCheckedChange={(checked) => setOptions((current) => ({ ...current, preserveNames: checked }))}
          />

          <LabeledField label="사용 모델">
            <Select value={options.model} onValueChange={(value) => setOptions((current) => ({ ...current, model: value }))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gemma4:26b-a4b-it-q4_K_M">gemma4:26b-a4b-it-q4_K_M</SelectItem>
                <SelectItem value="gemma4:12b">gemma4:12b</SelectItem>
                <SelectItem value="qwen2.5:14b">qwen2.5:14b</SelectItem>
                <SelectItem value="custom">사용자 지정 모델</SelectItem>
              </SelectContent>
            </Select>
          </LabeledField>

          <LabeledField label="Temperature">
            <Input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={options.temperature}
              onChange={(event) => setOptions((current) => ({ ...current, temperature: Number(event.target.value) }))}
            />
          </LabeledField>
        </CardContent>
      </Card>
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

function SwitchRow({
  checked,
  help,
  label,
  onCheckedChange,
}: {
  checked: boolean;
  help: string;
  label: string;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border p-3">
      <div>
        <div className="text-sm font-semibold">{label}</div>
        <div className="mt-1 text-xs text-muted-foreground">{help}</div>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}
