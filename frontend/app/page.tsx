"use client";

import { useEffect, useState } from "react";

import { GlossaryManager } from "@/components/glossary/GlossaryManager";
import { TranslationHistory } from "@/components/history/TranslationHistory";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppSection, AppSidebar } from "@/components/layout/AppSidebar";
import { CacheManagementCard } from "@/components/settings/CacheManagementCard";
import { MODEL_SETTINGS_STORAGE_KEY, ModelSettings } from "@/components/settings/ModelSettings";
import { HealthStatusCard } from "@/components/settings/HealthStatusCard";
import { TranslatePanel } from "@/components/translator/TranslatePanel";
import { TranslationViewer } from "@/components/translator/TranslationViewer";
import { useTranslationCache } from "@/hooks/useTranslationCache";
import { useGlossary } from "@/hooks/useGlossary";
import { useHealth } from "@/hooks/useHealth";
import { useTranslation } from "@/hooks/useTranslation";
import { useTranslationHistory } from "@/hooks/useTranslationHistory";
import { DEFAULT_MODEL_SETTINGS, type InputMode, type ModelSettings as ModelSettingsType } from "@/types/translation";

export default function Home() {
  const [activeSection, setActiveSection] = useState<AppSection>("translate");
  const [inputMode, setInputMode] = useState<InputMode>("url");
  const [modelSettings, setModelSettings] = useState<ModelSettingsType>(DEFAULT_MODEL_SETTINGS);
  const translation = useTranslation();
  const translationCache = useTranslationCache();
  const history = useTranslationHistory();
  const glossary = useGlossary();
  const health = useHealth();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const stored = window.localStorage.getItem(MODEL_SETTINGS_STORAGE_KEY);
      if (!stored) {
        return;
      }
      try {
        setModelSettings({ ...DEFAULT_MODEL_SETTINGS, ...(JSON.parse(stored) as Partial<ModelSettingsType>) });
      } catch {
        window.localStorage.removeItem(MODEL_SETTINGS_STORAGE_KEY);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const isGlossaryMutating =
    glossary.createTerm.isPending ||
    glossary.updateTerm.isPending ||
    glossary.deleteTerm.isPending ||
    glossary.permanentlyDeleteTerm.isPending ||
    glossary.importTerms.isPending ||
    glossary.createCandidate.isPending ||
    glossary.approveCandidate.isPending ||
    glossary.rejectCandidate.isPending;

  const isHistoryMutating = history.deleteHistory.isPending || history.clearHistory.isPending || history.openHistory.isPending;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[16rem_minmax(0,1fr)]">
      <AppSidebar activeSection={activeSection} onSectionChange={setActiveSection} />
      <main className="min-w-0 p-4 md:p-6 xl:p-8">
        <AppHeader
          activeSection={activeSection}
          inputMode={inputMode}
          healthState={health.state}
          onOpenHealthDetails={() => setActiveSection("settings")}
          pageCount={translation.pageCount}
          currentPageIndex={translation.currentPageIndex}
          progress={translation.progress}
          statusLabel={translation.statusLabel}
        />

        {activeSection === "translate" && (
          <TranslatePanel
            currentJob={translation.currentJob}
            errorMessage={translation.errorMessage}
            isTranslating={translation.isTranslating}
            modelSettings={modelSettings}
            onFetchUrl={translation.fetchUrlSource}
            onInputModeChange={setInputMode}
            onPrepareText={translation.prepareText}
            onSectionChange={setActiveSection}
            onTranslateTextAll={translation.translateTextAll}
            onTranslateTextFirst={translation.translateTextFirst}
            onTranslateUrlAll={translation.translateUrlAll}
            onTranslateUrlFirst={translation.translateUrlFirst}
          />
        )}

        {activeSection === "viewer" && (
          <TranslationViewer
            currentJob={translation.currentJob}
            currentPageIndex={translation.currentPageIndex}
            errorMessage={translation.errorMessage}
            isTranslating={translation.isTranslating}
            isSavingTranslation={translation.isSavingTranslation}
            isCreatingGlossaryCandidate={glossary.createCandidate.isPending}
            onCreateGlossaryCandidate={(request) => glossary.createCandidate.mutate(request)}
            onPageChange={translation.setCurrentPageIndex}
            onRetryChunk={translation.retryFailedChunk}
            onSavePageTranslation={translation.saveCurrentPageTranslation}
            onTranslateAllText={translation.translateTextAll}
            onTranslateAllUrl={translation.translateUrlAll}
            onTranslateCurrent={translation.translateCurrentPage}
            retryingChunkKey={translation.retryingChunkKey}
            setViewerMode={translation.setViewerMode}
            viewerMode={translation.viewerMode}
          />
        )}

        {activeSection === "history" && (
          <TranslationHistory
            histories={history.histories}
            isLoading={history.isLoading}
            isMutating={isHistoryMutating}
            clearHistory={() =>
              history.clearHistory.mutate(undefined, {
                onSuccess: () => {
                  translation.clearCurrentJob();
                },
              })
            }
            deleteHistory={(id) => {
              history.deleteHistory.mutate(id, {
                onSuccess: () => {
                  translation.clearCurrentJob(id);
                },
              });
            }}
            onOpenHistory={(jobId) => {
              history.openHistory.mutate(jobId, {
                onSuccess: (job) => {
                  translation.openJob(job);
                  setInputMode(job.inputMode);
                  setActiveSection("viewer");
                },
              });
            }}
          />
        )}

        {activeSection === "glossary" && (
          <GlossaryManager
            terms={glossary.terms}
            candidates={glossary.candidates}
            error={glossary.error}
            importTerms={(request, options) => glossary.importTerms.mutate(request, options)}
            isImporting={glossary.importTerms.isPending}
            isCandidatesLoading={glossary.isCandidatesLoading}
            isLoading={glossary.isLoading}
            isMutating={isGlossaryMutating}
            createTerm={(request) => glossary.createTerm.mutate(request)}
            approveCandidate={(id, request) => glossary.approveCandidate.mutate({ id, request })}
            updateTerm={(id, request) => glossary.updateTerm.mutate({ id, request })}
            deleteTerm={(id) => glossary.deleteTerm.mutate(id)}
            permanentlyDeleteTerm={(id, onSuccess) =>
              glossary.permanentlyDeleteTerm.mutate(id, { onSuccess })
            }
            rejectCandidate={(id) => glossary.rejectCandidate.mutate(id)}
          />
        )}

        {activeSection === "settings" && (
          <div className="space-y-6">
            <HealthStatusCard
              error={health.error}
              health={health.health}
              isFetching={health.isFetching}
              onRefresh={() => void health.refresh()}
            />
            <CacheManagementCard
              clearCache={() => translationCache.clearCache.mutate()}
              error={translationCache.clearCache.error}
              isClearing={translationCache.clearCache.isPending}
              isSuccess={translationCache.clearCache.isSuccess}
            />
            <ModelSettings settings={modelSettings} onSettingsChange={setModelSettings} />
          </div>
        )}
      </main>
    </div>
  );
}
