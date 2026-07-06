"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import {
  translateAll,
  translatePage,
  translateText,
  translateUrl,
} from "@/lib/api/translationApi";
import type {
  PageTranslateRequest,
  TranslationApiResult,
  TranslationJob,
  TranslationRequest,
  UrlTranslationRequest,
  ViewerMode,
} from "@/types/translation";

export function useTranslation() {
  const queryClient = useQueryClient();
  const [currentJob, setCurrentJob] = useState<TranslationJob | null>(null);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [viewerMode, setViewerMode] = useState<ViewerMode>("both");

  const applyResult = (result: TranslationApiResult) => {
    setCurrentJob(result.job);
    setCurrentPageIndex(result.response.current_page_index);
    queryClient.setQueryData(["translation", "current"], result.job);
    queryClient.invalidateQueries({ queryKey: ["history"] });
  };

  const translateTextMutation = useMutation({
    mutationFn: translateText,
    onSuccess: applyResult,
  });

  const translateUrlMutation = useMutation({
    mutationFn: translateUrl,
    onSuccess: applyResult,
  });

  const translatePageMutation = useMutation({
    mutationFn: ({ jobId, pageIndex, request }: { jobId: number; pageIndex: number; request: PageTranslateRequest }) =>
      translatePage(jobId, pageIndex, request),
    onSuccess: applyResult,
  });

  const translateAllMutation = useMutation({
    mutationFn: translateAll,
    onSuccess: applyResult,
  });

  const activePage = currentJob?.pages[currentPageIndex] ?? null;
  const translatedCount = currentJob?.pages.filter((page) => page.status === "completed").length ?? 0;
  const pageCount = currentJob?.pages.length ?? 0;
  const progress = pageCount === 0 ? 0 : Math.round((translatedCount / pageCount) * 100);
  const isTranslating =
    translateTextMutation.isPending ||
    translateUrlMutation.isPending ||
    translatePageMutation.isPending ||
    translateAllMutation.isPending;

  const statusLabel = useMemo(() => {
    if (isTranslating) {
      return "번역 중";
    }
    if (!currentJob) {
      return "대기 중";
    }
    if (translatedCount === pageCount && pageCount > 0) {
      return "전체 번역 완료";
    }
    if (translatedCount > 0) {
      return `page ${currentPageIndex + 1} 번역 완료`;
    }
    return "원문 준비 완료";
  }, [currentJob, currentPageIndex, isTranslating, pageCount, translatedCount]);

  return {
    activePage,
    currentJob,
    currentPageIndex,
    isTranslating,
    pageCount,
    progress,
    statusLabel,
    translatedCount,
    viewerMode,
    openJob(job: TranslationJob) {
      setCurrentJob(job);
      setCurrentPageIndex(0);
      setViewerMode("both");
      queryClient.setQueryData(["translation", "current"], job);
    },
    setCurrentPageIndex(index: number) {
      if (!currentJob) {
        setCurrentPageIndex(0);
        return;
      }
      setCurrentPageIndex(Math.min(Math.max(index, 0), Math.max(currentJob.pages.length - 1, 0)));
    },
    setViewerMode,
    translateCurrentPage(request: PageTranslateRequest) {
      if (!currentJob) {
        return;
      }
      translatePageMutation.mutate({
        jobId: currentJob.jobId,
        pageIndex: currentPageIndex,
        request,
      });
    },
    translateTextFirst(request: TranslationRequest) {
      translateTextMutation.mutate({
        ...request,
        translate_scope: "first_page",
        page_index: 0,
      });
    },
    translateUrlFirst(request: UrlTranslationRequest) {
      setViewerMode(request.view_mode);
      translateUrlMutation.mutate({
        ...request,
        translate_scope: "first_page",
        page_index: 0,
      });
    },
    translateTextAll(request: TranslationRequest) {
      translateAllMutation.mutate({
        ...request,
        translate_scope: "all_pages",
      });
    },
    translateUrlAll(request: UrlTranslationRequest) {
      setViewerMode(request.view_mode);
      translateAllMutation.mutate({
        ...request,
        translate_scope: "all_pages",
      });
    },
  };
}
