"use client";

import { BookOpenText, Clipboard, Languages, Pencil, RotateCw, Save, X } from "lucide-react";
import { useState } from "react";

import { PageNavigator, PageStepButtons } from "@/components/translator/PageNavigator";
import { Badge } from "@/components/ui/badge";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { createPageTranslateRequest, createTranslationRequest, createUrlTranslationRequest } from "@/lib/translationRequests";
import type { GlossaryCandidateCreateRequest, GlossarySourceLanguage } from "@/types/glossary";
import type { TranslationJob, TranslationRequest, UrlTranslationRequest, ViewerMode } from "@/types/translation";

export function TranslationViewer({
  currentJob,
  currentPageIndex,
  errorMessage,
  isTranslating,
  isCreatingGlossaryCandidate = false,
  isSavingTranslation = false,
  onCreateGlossaryCandidate,
  onPageChange,
  onRetryChunk,
  onSavePageTranslation,
  onTranslateAllText,
  onTranslateAllUrl,
  onTranslateCurrent,
  retryingChunkKey,
  setViewerMode,
  viewerMode,
}: {
  currentJob: TranslationJob | null;
  currentPageIndex: number;
  errorMessage: string | null;
  isTranslating: boolean;
  isCreatingGlossaryCandidate?: boolean;
  isSavingTranslation?: boolean;
  onCreateGlossaryCandidate?: (request: GlossaryCandidateCreateRequest) => void;
  onPageChange: (index: number) => void;
  onRetryChunk: (pageIndex: number, chunkIndex: number) => void;
  onSavePageTranslation?: (translatedText: string, onSaved?: () => void) => void;
  onTranslateAllText: (request: TranslationRequest) => void;
  onTranslateAllUrl: (request: UrlTranslationRequest) => void;
  onTranslateCurrent: (request: ReturnType<typeof createPageTranslateRequest>) => void;
  retryingChunkKey: string | null;
  setViewerMode: (mode: ViewerMode) => void;
  viewerMode: ViewerMode;
}) {
  const [copyLabel, setCopyLabel] = useState("복사");
  const [isCandidateMode, setIsCandidateMode] = useState(false);
  const [isCandidateDialogOpen, setIsCandidateDialogOpen] = useState(false);
  const [selectedSourceTerm, setSelectedSourceTerm] = useState("");
  const [selectedTargetTerm, setSelectedTargetTerm] = useState("");
  const [candidateMessage, setCandidateMessage] = useState("");
  const [isEditingTranslation, setIsEditingTranslation] = useState(false);
  const [editedTranslation, setEditedTranslation] = useState("");
  const [editingTranslationKey, setEditingTranslationKey] = useState<string | null>(null);
  const activePage = currentJob?.pages[currentPageIndex] ?? null;
  const activePageKey = currentJob ? `${currentJob.jobId}:${currentPageIndex}` : null;
  const isEditingCurrentTranslation =
    isEditingTranslation && editingTranslationKey === activePageKey;
  const pageCount = currentJob?.pages.length ?? 0;
  const failedChunks =
    currentJob?.chunks.filter(
      (chunk) => chunk.pageIndex === currentPageIndex && chunk.status === "failed",
    ) ?? [];

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

  const canStartCandidateMode = Boolean(
    currentJob && activePage?.sourceText && activePage?.translatedText && onCreateGlossaryCandidate,
  );
  const canEditTranslation = Boolean(
    currentJob?.jobId &&
      activePage?.translatedText &&
      activePage.status === "completed" &&
      onSavePageTranslation,
  );
  const canSubmitCandidate = Boolean(selectedSourceTerm.trim() && selectedTargetTerm.trim());

  const startCandidateMode = () => {
    if (!canStartCandidateMode) {
      return;
    }
    setViewerMode("both");
    setIsCandidateMode(true);
    setIsCandidateDialogOpen(false);
    setSelectedSourceTerm("");
    setSelectedTargetTerm("");
    setCandidateMessage("번역문에서 후보 번역어를 드래그한 뒤, 원문에서 대응 원어를 드래그하세요.");
  };

  const cancelCandidateMode = () => {
    setIsCandidateMode(false);
    setIsCandidateDialogOpen(false);
    setSelectedSourceTerm("");
    setSelectedTargetTerm("");
    setCandidateMessage("");
  };

  const closeTranslationEditor = () => {
    setIsEditingTranslation(false);
    setEditingTranslationKey(null);
    setEditedTranslation("");
  };

  const startEditingTranslation = () => {
    if (!canEditTranslation || !activePage || !activePageKey) {
      return;
    }
    cancelCandidateMode();
    setEditedTranslation(activePage.translatedText);
    setEditingTranslationKey(activePageKey);
    setIsEditingTranslation(true);
  };

  const cancelEditingTranslation = () => {
    closeTranslationEditor();
  };

  const saveEditedTranslation = () => {
    if (!onSavePageTranslation || !editedTranslation.trim()) {
      return;
    }
    onSavePageTranslation(editedTranslation, closeTranslationEditor);
  };

  const changePage = (index: number) => {
    closeTranslationEditor();
    onPageChange(index);
  };

  const captureCandidateSelection = (side: "source" | "target") => {
    if (!isCandidateMode) {
      return;
    }
    const selectedText = window.getSelection()?.toString().trim() ?? "";
    if (!selectedText) {
      return;
    }
    if (side === "source") {
      setSelectedSourceTerm(selectedText);
      setCandidateMessage("원어가 선택되었습니다. 번역어도 선택한 뒤 후보 등록을 확인하세요.");
      return;
    }
    setSelectedTargetTerm(selectedText);
    setCandidateMessage("번역어가 선택되었습니다. 원어도 선택한 뒤 후보 등록을 확인하세요.");
  };

  const submitCandidate = () => {
    if (!currentJob || !activePage || !onCreateGlossaryCandidate) {
      return;
    }
    const sourceLang = toGlossarySourceLanguage(currentJob.sourceLang);
    if (!sourceLang) {
      setCandidateMessage("source_lang이 auto인 상태에서는 후보를 등록할 수 없습니다. 번역 완료 후 다시 시도하세요.");
      return;
    }
    const sourceTerm = selectedSourceTerm.trim();
    const suggestedTargetTerm = selectedTargetTerm.trim();
    if (!sourceTerm || !suggestedTargetTerm) {
      return;
    }

    onCreateGlossaryCandidate({
      source_lang: sourceLang,
      target_lang: currentJob.targetLang,
      source_term: sourceTerm,
      suggested_target_term: suggestedTargetTerm,
      source_text: activePage.sourceText,
      model_translation: activePage.translatedText,
      user_corrected_translation: activePage.translatedText,
    });
    setIsCandidateDialogOpen(false);
    setIsCandidateMode(false);
    setCandidateMessage("용어집 후보를 등록했습니다. 용어집 화면에서 승인하거나 거절할 수 있습니다.");
  };

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <CardTitle>번역본 보기</CardTitle>
            <CardDescription className="mt-2">page 단위로 원문과 한국어 번역본을 확인합니다.</CardDescription>
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
            <Button
              type="button"
              variant="outline"
              onClick={startCandidateMode}
              disabled={
                !canStartCandidateMode ||
                isTranslating ||
                isCreatingGlossaryCandidate ||
                isEditingCurrentTranslation
              }
            >
              용어 후보 만들기
            </Button>
          </div>
        </div>

        {currentJob && (
          <div className="rounded-md border bg-muted/30 p-3 text-sm">
            <div className="font-semibold">{currentJob.title}</div>
            <div className="mt-1 flex flex-wrap gap-2 text-muted-foreground">
              <span>{currentJob.inputMode === "url" ? "URL" : "텍스트"}</span>
              {currentJob.sourceAuthor && <span>작가: {currentJob.sourceAuthor}</span>}
              {currentJob.sourceUrl && <span className="truncate">원문: {currentJob.sourceUrl}</span>}
              <span>모델: {currentJob.model}</span>
              <span>Prompt: {currentJob.promptVersion}</span>
            </div>
          </div>
        )}

        {errorMessage && <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{errorMessage}</div>}

        <Separator />
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <PageNavigator currentPageIndex={currentPageIndex} onPageChange={changePage} pageCount={pageCount} />
          <div className="w-full xl:w-56">
            <Select value={viewerMode} onValueChange={(value) => setViewerMode(value as ViewerMode)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="translation">번역본만 보기</SelectItem>
                <SelectItem value="both">원문 + 번역본 같이 보기</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {!currentJob ? (
          <EmptyViewer />
        ) : (
          <div className="space-y-4">
            <div className={viewerMode === "both" ? "grid gap-4 xl:grid-cols-2" : "grid gap-4"}>
              {viewerMode === "both" && (
                <ViewerPanel
                  title="원문"
                  meta={`page ${currentPageIndex + 1} / ${pageCount}`}
                  onTextSelect={() => captureCandidateSelection("source")}
                >
                  {activePage?.sourceText || "원문이 없습니다."}
                </ViewerPanel>
              )}
              <ViewerPanel
                title="한국어 번역본"
                meta={<Badge variant={activePage?.status === "completed" ? "success" : activePage?.status === "failed" ? "destructive" : "secondary"}>{statusLabel(activePage?.status)}</Badge>}
                action={
                  <div className="flex shrink-0 gap-2">
                    {isEditingCurrentTranslation ? (
                      <>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={cancelEditingTranslation}
                          disabled={isSavingTranslation}
                        >
                          <X className="h-4 w-4" />
                          취소
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          onClick={saveEditedTranslation}
                          disabled={isSavingTranslation || !editedTranslation.trim()}
                        >
                          <Save className="h-4 w-4" />
                          {isSavingTranslation ? "저장 중" : "저장"}
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={startEditingTranslation}
                          disabled={!canEditTranslation || isTranslating || isSavingTranslation}
                        >
                          <Pencil className="h-4 w-4" />
                          수정
                        </Button>
                        <Button type="button" variant="outline" size="sm" onClick={copyTranslation}>
                          <Clipboard className="h-4 w-4" />
                          {copyLabel}
                        </Button>
                      </>
                    )}
                  </div>
                }
                onTextSelect={() => captureCandidateSelection("target")}
              >
                {isEditingCurrentTranslation ? (
                  <Textarea
                    aria-label="번역문 수정"
                    className="min-h-96 resize-y leading-7"
                    disabled={isSavingTranslation}
                    value={editedTranslation}
                    onChange={(event) => setEditedTranslation(event.target.value)}
                  />
                ) : (
                  activePage?.translatedText || "아직 이 page의 번역 결과가 없습니다. 현재 page 번역 또는 전체 번역을 실행하세요."
                )}
              </ViewerPanel>
            </div>
            {isCandidateMode || candidateMessage ? (
              <section className="space-y-3 rounded-md border bg-muted/30 p-4 text-sm">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="space-y-2">
                    <p className="font-semibold">용어집 후보 선택</p>
                    {candidateMessage ? <p className="text-muted-foreground">{candidateMessage}</p> : null}
                    <div className="flex flex-wrap gap-2">
                      <Badge variant={selectedTargetTerm ? "success" : "secondary"}>
                        번역어: {selectedTargetTerm || "미선택"}
                      </Badge>
                      <Badge variant={selectedSourceTerm ? "success" : "secondary"}>
                        원어: {selectedSourceTerm || "미선택"}
                      </Badge>
                    </div>
                  </div>
                  {isCandidateMode ? (
                    <div className="flex shrink-0 gap-2">
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => setIsCandidateDialogOpen(true)}
                        disabled={!canSubmitCandidate || isCreatingGlossaryCandidate}
                      >
                        후보 등록 확인
                      </Button>
                      <Button type="button" size="sm" variant="outline" onClick={cancelCandidateMode}>
                        취소
                      </Button>
                    </div>
                  ) : null}
                </div>
              </section>
            ) : null}
            {failedChunks.length > 0 ? (
              <section className="space-y-3 rounded-md border border-destructive/30 bg-destructive/5 p-4">
                <div>
                  <h3 className="font-semibold text-destructive">실패 chunk</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    현재 페이지에서 실패한 chunk만 개별 재시도할 수 있습니다.
                  </p>
                </div>
                {failedChunks.map((chunk) => {
                  const key = `${currentPageIndex}:${chunk.index}`;
                  const retrying = retryingChunkKey === key;
                  return (
                    <div key={chunk.id} className="rounded-md border bg-background p-3 text-sm">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="destructive">Chunk {chunk.index + 1}</Badge>
                            <span className="text-muted-foreground">재시도 {chunk.retryCount}회</span>
                          </div>
                          <p className="whitespace-pre-wrap">{chunk.sourceText.slice(0, 240)}</p>
                          {chunk.errorMessage ? <p className="text-destructive">{chunk.errorMessage}</p> : null}
                        </div>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={isTranslating || retrying}
                          onClick={() => onRetryChunk(currentPageIndex, chunk.index)}
                        >
                          <RotateCw className={retrying ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
                          Chunk {chunk.index + 1} {retrying ? "재시도 중" : "재시도"}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </section>
            ) : null}
            <div className="flex flex-col gap-3 rounded-md border bg-muted/30 p-3 sm:flex-row sm:items-center sm:justify-between">
              <span className="text-sm text-muted-foreground">page {currentPageIndex + 1} / {pageCount}</span>
              <PageStepButtons currentPageIndex={currentPageIndex} onPageChange={changePage} pageCount={pageCount} />
            </div>
          </div>
        )}
      </CardContent>
      <Dialog open={isCandidateDialogOpen} onOpenChange={setIsCandidateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>용어집 후보 등록</DialogTitle>
            <DialogDescription>
              선택한 원어와 번역어를 용어집 후보로 저장합니다. 등록 후 용어집 화면에서 승인할 수 있습니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 text-sm">
            <div className="rounded-md border bg-muted/30 p-3 text-center text-base font-semibold">
              {selectedSourceTerm || "원어 미선택"} → {selectedTargetTerm || "번역어 미선택"}
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <CandidatePreview label="원문 문맥" value={activePage?.sourceText ?? ""} />
              <CandidatePreview label="번역문 문맥" value={activePage?.translatedText ?? ""} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setIsCandidateDialogOpen(false)}>
              취소
            </Button>
            <Button
              type="button"
              onClick={submitCandidate}
              disabled={!canSubmitCandidate || isCreatingGlossaryCandidate}
            >
              {isCreatingGlossaryCandidate ? "등록 중..." : "후보 등록"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

function ViewerPanel({
  action,
  children,
  meta,
  onTextSelect,
  title,
}: {
  action?: React.ReactNode;
  children: React.ReactNode;
  meta: React.ReactNode;
  onTextSelect?: () => void;
  title: string;
}) {
  return (
    <article className="flex min-h-96 flex-col overflow-hidden rounded-md border bg-white">
      <header className="flex min-h-12 items-center justify-between gap-3 border-b bg-muted/50 px-4 py-3 text-sm font-semibold">
        <div className="flex min-w-0 items-center gap-2">
          <span>{title}</span>
          <span className="truncate text-xs font-normal text-muted-foreground">{meta}</span>
        </div>
        {action}
      </header>
      <div className="whitespace-pre-wrap p-4 text-sm leading-7" onMouseUp={onTextSelect}>
        {children}
      </div>
    </article>
  );
}

function CandidatePreview({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border p-3">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap">{value}</p>
    </div>
  );
}

function EmptyViewer() {
  return (
    <div className="grid min-h-80 place-items-center rounded-md border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">
      아직 준비된 원문이 없습니다. 번역 작업 화면에서 URL 원문을 가져오거나 텍스트를 준비하세요.
    </div>
  );
}

function statusLabel(status: string | undefined): string {
  if (status === "completed") {
    return "완료";
  }
  if (status === "failed") {
    return "실패";
  }
  if (status === "fetched") {
    return "원문 준비";
  }
  return "대기";
}

function toGlossarySourceLanguage(sourceLang: TranslationJob["sourceLang"]): GlossarySourceLanguage | null {
  return sourceLang === "auto" ? null : sourceLang;
}
