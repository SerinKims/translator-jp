"use client";

import { BookOpenText, Clock3, Download, Languages } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { AppSection } from "@/components/layout/AppSidebar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { createOptionsFromSettings, createTranslationRequest, createUrlTranslationRequest } from "@/lib/translationRequests";
import type {
  InputMode,
  ModelSettings,
  SourceLanguage,
  TranslationJob,
  TranslationOptions,
  TranslationRequest,
  UrlTranslationRequest,
  ViewerMode,
} from "@/types/translation";
import type { PixivFetchRequest } from "@/types/source";

const sourceTextHint = `吾輩は猫である。名前はまだ無い。
[newpage]
どこで生れたかとんと見当がつかぬ。`;

export function TranslatePanel({
  currentJob,
  errorMessage,
  isTranslating,
  modelSettings,
  onFetchUrl,
  onInputModeChange,
  onPrepareText,
  onSectionChange,
  onTranslateTextAll,
  onTranslateTextFirst,
  onTranslateUrlAll,
  onTranslateUrlFirst,
}: {
  currentJob: TranslationJob | null;
  errorMessage: string | null;
  isTranslating: boolean;
  modelSettings: ModelSettings;
  onFetchUrl: (request: PixivFetchRequest, sourceLang: SourceLanguage, options: TranslationOptions) => void;
  onInputModeChange: (mode: InputMode) => void;
  onPrepareText: (text: string, sourceLang: SourceLanguage, options: TranslationOptions) => void;
  onSectionChange: (section: AppSection) => void;
  onTranslateTextAll: (request: TranslationRequest) => void;
  onTranslateTextFirst: (request: TranslationRequest) => void;
  onTranslateUrlAll: (request: UrlTranslationRequest) => void;
  onTranslateUrlFirst: (request: UrlTranslationRequest) => void;
}) {
  const [inputMode, setInputMode] = useState<InputMode>("url");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [sourceLang, setSourceLang] = useState<SourceLanguage>("ja");
  const [viewerMode, setViewerMode] = useState<ViewerMode>("both");
  const [options, setOptions] = useState<TranslationOptions>(() => createOptionsFromSettings(modelSettings));

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setOptions((current) => createOptionsFromSettings(modelSettings, current));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [modelSettings]);

  const pageCount = useMemo(() => splitPageCount(sourceText), [sourceText]);
  const isUrlReady = sourceUrl.trim().length > 0;
  const isTextReady = sourceText.trim().length > 0;

  const updateMode = (mode: InputMode) => {
    setInputMode(mode);
    onInputModeChange(mode);
  };

  const buildOptions = () => createOptionsFromSettings(modelSettings, options);

  const buildFetchRequest = (mergedOptions: TranslationOptions): PixivFetchRequest => ({
    url: sourceUrl.trim(),
    translate_after_fetch: false,
    model_name: mergedOptions.model,
    prompt_version: mergedOptions.promptVersion,
    source_lang: sourceLang,
    target_lang: "ko",
    style: mergedOptions.style,
    honorific_policy: mergedOptions.honorificPolicy,
    preserve_names: mergedOptions.preserveNames,
    think: mergedOptions.think,
    options: {
      temperature: mergedOptions.temperature,
      top_p: mergedOptions.topP,
      num_ctx: mergedOptions.contextWindow,
      num_predict: mergedOptions.maxTokens,
    },
  });

  const fetchUrl = () => {
    const mergedOptions = buildOptions();
    onFetchUrl(buildFetchRequest(mergedOptions), sourceLang, mergedOptions);
    onSectionChange("viewer");
  };

  const prepareText = () => {
    const mergedOptions = buildOptions();
    onPrepareText(sourceText, sourceLang, mergedOptions);
    onSectionChange("viewer");
  };

  const runFirst = () => {
    const mergedOptions = buildOptions();
    if (inputMode === "url") {
      onTranslateUrlFirst(
        createUrlTranslationRequest({
          url: sourceUrl.trim(),
          sourceLang,
          options: mergedOptions,
          viewerMode,
        }),
      );
    } else {
      onPrepareText(sourceText, sourceLang, mergedOptions);
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
          url: sourceUrl.trim(),
          sourceLang,
          options: mergedOptions,
          viewerMode,
        }),
      );
    } else {
      onPrepareText(sourceText, sourceLang, mergedOptions);
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
          <CardDescription>pixiv URL 또는 붙여넣은 텍스트를 백엔드 API에 전달합니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {errorMessage && <ErrorBox message={errorMessage} />}

          <Tabs value={inputMode} onValueChange={(value) => updateMode(value as InputMode)}>
            <TabsList>
              <TabsTrigger value="url">URL</TabsTrigger>
              <TabsTrigger value="text">텍스트</TabsTrigger>
            </TabsList>

            <TabsContent value="url" className="space-y-4">
              <LabeledField label="pixiv 소설 URL">
                <Input value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://www.pixiv.net/novel/show.php?id=12345" />
              </LabeledField>
              <LabeledField label="보기 방식">
                <Select value={viewerMode} onValueChange={(value) => setViewerMode(value as ViewerMode)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="translation">번역본만 보기</SelectItem>
                    <SelectItem value="both">원문 + 번역본 같이 보기</SelectItem>
                  </SelectContent>
                </Select>
              </LabeledField>
              {currentJob?.inputMode === "url" && (
                <div className="rounded-md border bg-muted/30 p-3 text-sm">
                  <div className="font-semibold">{currentJob.title}</div>
                  <div className="mt-1 text-muted-foreground">
                    {currentJob.sourceAuthor || "작가 정보 없음"} · {currentJob.pages.length} page
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="text" className="space-y-3">
              <LabeledField label="원문 텍스트">
                <Textarea
                  value={sourceText}
                  onChange={(event) => setSourceText(event.target.value)}
                  className="min-h-72 font-mono leading-7"
                  placeholder={sourceTextHint}
                />
              </LabeledField>
              <Badge variant="secondary">{pageCount} page</Badge>
            </TabsContent>
          </Tabs>

          <div className="grid gap-4 md:grid-cols-2">
            <LabeledField label="원문 언어">
              <Select value={sourceLang} onValueChange={(value) => setSourceLang(value as SourceLanguage)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">자동 감지</SelectItem>
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
            {inputMode === "url" ? (
              <Button type="button" variant="outline" onClick={fetchUrl} disabled={isTranslating || !isUrlReady}>
                <Download className="h-4 w-4" />
                원문 가져오기
              </Button>
            ) : (
              <Button type="button" variant="outline" onClick={prepareText} disabled={isTranslating || !isTextReady}>
                <Download className="h-4 w-4" />
                원문 준비
              </Button>
            )}
            <Button type="button" onClick={runFirst} disabled={isTranslating || (inputMode === "url" ? !isUrlReady : !isTextReady)}>
              <Languages className="h-4 w-4" />첫 page 번역
            </Button>
            <Button type="button" variant="success" onClick={runAll} disabled={isTranslating || (inputMode === "url" ? !isUrlReady : !isTextReady)}>
              <BookOpenText className="h-4 w-4" />
              전체 번역
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
          <CardDescription>한국어 웹소설 문체로 번역하며, 백엔드가 지원하지 않는 모델 설정은 화면 상태로 보관합니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <SwitchRow
            label="용어집 사용"
            help="등록된 용어를 우선 적용합니다."
            checked={options.useGlossary}
            onCheckedChange={(checked) => setOptions((current) => ({ ...current, useGlossary: checked }))}
          />
          <SwitchRow
            label="캐시 사용"
            help="같은 원문의 기존 번역 결과를 재사용합니다."
            checked={options.useCache}
            onCheckedChange={(checked) => setOptions((current) => ({ ...current, useCache: checked }))}
          />
          <SwitchRow
            label="고유명사 보존"
            help="인명과 지명 번역 흔들림을 줄입니다."
            checked={options.preserveNames}
            onCheckedChange={(checked) => setOptions((current) => ({ ...current, preserveNames: checked }))}
          />

          <LabeledField label="Style">
            <Select value={options.style} onValueChange={(value) => setOptions((current) => ({ ...current, style: value as TranslationOptions["style"] }))}>
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
              value={options.honorificPolicy}
              onValueChange={(value) => setOptions((current) => ({ ...current, honorificPolicy: value as TranslationOptions["honorificPolicy"] }))}
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
            <Select value={thinkToValue(options.think)} onValueChange={(value) => setOptions((current) => ({ ...current, think: valueToThink(value) }))}>
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
    <div className="flex items-center justify-between gap-4 rounded-md border p-3">
      <div>
        <div className="text-sm font-semibold">{label}</div>
        <div className="mt-1 text-xs text-muted-foreground">{help}</div>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{message}</div>;
}

function splitPageCount(text: string): number {
  const pages = text
    .split(/\r?\n?\[newpage\]\r?\n?/i)
    .map((page) => page.trim())
    .filter(Boolean);
  return Math.max(pages.length, text.trim() ? 1 : 0);
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
