"use client";

import { useState } from "react";

import { GlossaryManager } from "@/components/glossary/GlossaryManager";
import { TranslationHistory } from "@/components/history/TranslationHistory";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppSection, AppSidebar } from "@/components/layout/AppSidebar";
import { ModelSettings } from "@/components/settings/ModelSettings";
import { TranslatePanel } from "@/components/translator/TranslatePanel";
import { TranslationViewer } from "@/components/translator/TranslationViewer";
import { useGlossary } from "@/hooks/useGlossary";
import { useTranslation } from "@/hooks/useTranslation";
import { useTranslationHistory } from "@/hooks/useTranslationHistory";
import { DEFAULT_MODEL_SETTINGS, type InputMode, type ModelSettings as ModelSettingsType } from "@/types/translation";

export default function Home() {
  const [activeSection, setActiveSection] = useState<AppSection>("translate");
  const [inputMode, setInputMode] = useState<InputMode>("url");
  const [modelSettings, setModelSettings] = useState<ModelSettingsType>(DEFAULT_MODEL_SETTINGS);
  const translation = useTranslation();
  const history = useTranslationHistory();
  const glossary = useGlossary();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[16rem_minmax(0,1fr)]">
      <AppSidebar activeSection={activeSection} onSectionChange={setActiveSection} />
      <main className="min-w-0 p-4 md:p-6 xl:p-8">
        <AppHeader
          activeSection={activeSection}
          inputMode={inputMode}
          pageCount={translation.pageCount}
          currentPageIndex={translation.currentPageIndex}
          progress={translation.progress}
          statusLabel={translation.statusLabel}
        />

        {activeSection === "translate" && (
          <TranslatePanel
            isTranslating={translation.isTranslating}
            modelSettings={modelSettings}
            onInputModeChange={setInputMode}
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
            isTranslating={translation.isTranslating}
            onPageChange={translation.setCurrentPageIndex}
            onTranslateAllText={translation.translateTextAll}
            onTranslateAllUrl={translation.translateUrlAll}
            onTranslateCurrent={translation.translateCurrentPage}
            setViewerMode={translation.setViewerMode}
            viewerMode={translation.viewerMode}
          />
        )}

        {activeSection === "history" && (
          <TranslationHistory
            histories={history.histories}
            clearHistory={() => history.clearHistory.mutate()}
            deleteHistory={(id) => history.deleteHistory.mutate(id)}
            onOpenHistory={(job) => {
              translation.openJob(job);
              setInputMode(job.inputMode);
              setActiveSection("viewer");
            }}
          />
        )}

        {activeSection === "glossary" && (
          <GlossaryManager
            terms={glossary.terms}
            createTerm={(request) => glossary.createTerm.mutate(request)}
            updateTerm={(id, request) => glossary.updateTerm.mutate({ id, request })}
            deleteTerm={(id) => glossary.deleteTerm.mutate(id)}
          />
        )}

        {activeSection === "settings" && <ModelSettings settings={modelSettings} onSettingsChange={setModelSettings} />}
      </main>
    </div>
  );
}
