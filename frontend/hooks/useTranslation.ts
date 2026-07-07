"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { getErrorMessage } from "@/lib/api/client";
import { fetchPixivSource } from "@/lib/api/sourceApi";
import {
  createPendingJobFromSource,
  createPendingJobFromText,
  getTranslationJob,
  translateAll,
  translatePage,
  translateText,
  translateUrl,
} from "@/lib/api/translationApi";
import { createPageTranslateRequest } from "@/lib/translationRequests";
import type { PixivFetchRequest } from "@/types/source";
import type {
  PageTranslateRequest,
  SourceLanguage,
  TranslationApiResult,
  TranslationJob,
  TranslationOptions,
  TranslationRequest,
  UrlTranslationRequest,
  ViewerMode,
} from "@/types/translation";

export function useTranslation() {
  const queryClient = useQueryClient();
  const [currentJob, setCurrentJob] = useState<TranslationJob | null>(null);
  const [currentPageIndex, setCurrentPageIndexState] = useState(0);
  const [viewerMode, setViewerMode] = useState<ViewerMode>("both");
  const [progressMessage, setProgressMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const applyJob = (job: TranslationJob) => {
    setCurrentJob(job);
    setCurrentPageIndexState(job.currentPageIndex);
    queryClient.setQueryData(["translation", "current"], job);
    queryClient.invalidateQueries({ queryKey: ["history"] });
  };

  const applyResult = (result: TranslationApiResult) => {
    applyJob(result.job);
    setErrorMessage(null);
    setProgressMessage("");
  };

  const onError = (error: unknown) => {
    setErrorMessage(getErrorMessage(error));
    setProgressMessage("");
  };

  const fetchUrlSourceMutation = useMutation({
    mutationFn: async ({
      options,
      request,
      sourceLang,
    }: {
      request: PixivFetchRequest;
      sourceLang: SourceLanguage;
      options: TranslationOptions;
    }) => {
      setProgressMessage("URL 원문을 가져오는 중입니다.");
      const source = await fetchPixivSource(request);
      return createPendingJobFromSource({ source, sourceLang, options });
    },
    onSuccess: (job) => {
      applyJob(job);
      setErrorMessage(null);
      setProgressMessage("");
    },
    onError,
  });

  const translateTextMutation = useMutation({
    mutationFn: translateText,
    onSuccess: applyResult,
    onError,
  });

  const translateUrlMutation = useMutation({
    mutationFn: translateUrl,
    onSuccess: applyResult,
    onError,
  });

  const translatePageMutation = useMutation({
    mutationFn: ({ jobId, pageIndex, request }: { jobId: number; pageIndex: number; request: PageTranslateRequest }) =>
      translatePage(jobId, pageIndex, request),
    onSuccess: applyResult,
    onError,
  });

  const translateAllMutation = useMutation({
    mutationFn: translateAll,
    onSuccess: applyResult,
    onError,
  });

  const translateUrlAllMutation = useMutation({
    mutationFn: async (request: UrlTranslationRequest) => {
      let job = currentJob;
      if (!job || job.inputMode !== "url" || job.sourceUrl !== request.url || job.jobId === 0) {
        setProgressMessage("URL 원문을 가져오는 중입니다.");
        const source = await fetchPixivSource({
          url: request.url,
          translate_after_fetch: false,
          model_name: request.model_name,
          source_lang: request.source_lang,
          target_lang: request.target_lang,
          style: request.style,
          honorific_policy: request.honorific_policy,
          preserve_names: request.preserve_names,
          think: request.think,
          options: request.options,
        });
        job = createPendingJobFromSource({
          source,
          sourceLang: request.source_lang,
          options: requestToUiOptions(request),
        });
        setCurrentJob(job);
      }

      let latest = job;
      for (const page of job.pages) {
        setProgressMessage(`${page.index + 1} / ${job.pages.length} page 번역 중입니다.`);
        const result = await translatePage(job.jobId, page.index, createPageTranslateRequest(latest));
        latest = result.job;
        setCurrentJob(latest);
        queryClient.invalidateQueries({ queryKey: ["history"] });
      }
      return { response: await responseFromJob(latest), job: latest };
    },
    onSuccess: applyResult,
    onError,
  });

  const translateUrlFirstMutation = useMutation({
    mutationFn: async (request: UrlTranslationRequest) => {
      let job = currentJob;
      if (!job || job.inputMode !== "url" || job.sourceUrl !== request.url || job.jobId === 0) {
        setProgressMessage("URL 원문을 가져오는 중입니다.");
        const source = await fetchPixivSource({
          url: request.url,
          translate_after_fetch: false,
          model_name: request.model_name,
          source_lang: request.source_lang,
          target_lang: request.target_lang,
          style: request.style,
          honorific_policy: request.honorific_policy,
          preserve_names: request.preserve_names,
          think: request.think,
          options: request.options,
        });
        job = createPendingJobFromSource({
          source,
          sourceLang: request.source_lang,
          options: requestToUiOptions(request),
        });
        setCurrentJob(job);
      }
      setProgressMessage("첫 page를 번역하는 중입니다.");
      return translatePage(job.jobId, 0, createPageTranslateRequest(job));
    },
    onSuccess: applyResult,
    onError,
  });

  const isTranslating =
    fetchUrlSourceMutation.isPending ||
    translateTextMutation.isPending ||
    translateUrlMutation.isPending ||
    translatePageMutation.isPending ||
    translateAllMutation.isPending ||
    translateUrlAllMutation.isPending ||
    translateUrlFirstMutation.isPending;

  const activePage = currentJob?.pages[currentPageIndex] ?? null;
  const translatedCount = currentJob?.pages.filter((page) => page.status === "completed").length ?? 0;
  const pageCount = currentJob?.pages.length ?? 0;
  const progress = pageCount === 0 ? 0 : Math.round((translatedCount / pageCount) * 100);

  const statusLabel = useMemo(() => {
    if (isTranslating) {
      return progressMessage || "번역 중";
    }
    if (!currentJob) {
      return "대기 중";
    }
    if (currentJob.status === "failed") {
      return "실패";
    }
    if (translatedCount === pageCount && pageCount > 0) {
      return "전체 번역 완료";
    }
    if (translatedCount > 0) {
      return `${translatedCount} / ${pageCount} page 완료`;
    }
    if (currentJob.inputMode === "url") {
      return "원문 가져오기 완료";
    }
    return "원문 준비 완료";
  }, [currentJob, isTranslating, pageCount, progressMessage, translatedCount]);

  return {
    activePage,
    currentJob,
    currentPageIndex,
    errorMessage,
    isTranslating,
    pageCount,
    progress,
    statusLabel,
    translatedCount,
    viewerMode,
    fetchUrlSource(request: PixivFetchRequest, sourceLang: SourceLanguage, options: TranslationOptions) {
      fetchUrlSourceMutation.mutate({ request, sourceLang, options });
    },
    openJob(job: TranslationJob) {
      applyJob({ ...job, currentPageIndex: 0 });
      setViewerMode("both");
    },
    prepareText(text: string, sourceLang: SourceLanguage, options: TranslationOptions) {
      applyJob(createPendingJobFromText({ text, sourceLang, options }));
      setErrorMessage(null);
    },
    setCurrentPageIndex(index: number) {
      if (!currentJob) {
        setCurrentPageIndexState(0);
        return;
      }
      setCurrentPageIndexState(Math.min(Math.max(index, 0), Math.max(currentJob.pages.length - 1, 0)));
    },
    setViewerMode,
    translateCurrentPage(request: PageTranslateRequest) {
      if (!currentJob || currentJob.jobId === 0) {
        if (currentJob) {
          translateTextMutation.mutate({
            text: currentJob.pages.map((page) => page.sourceText).join("\n\n[newpage]\n\n"),
            model_name: currentJob.options.model,
            source_lang: currentJob.sourceLang,
            target_lang: "ko",
            translate_scope: "current_page",
            page_index: currentPageIndex,
            style: currentJob.options.style,
            honorific_policy: currentJob.options.honorificPolicy,
            preserve_names: currentJob.options.preserveNames,
            use_glossary: currentJob.options.useGlossary,
            use_cache: currentJob.options.useCache,
            stream: false,
            think: currentJob.options.think,
            options: {
              temperature: currentJob.options.temperature,
              top_p: currentJob.options.topP,
              num_ctx: currentJob.options.contextWindow,
              num_predict: currentJob.options.maxTokens,
            },
          });
        }
        return;
      }
      translatePageMutation.mutate({
        jobId: currentJob.jobId,
        pageIndex: currentPageIndex,
        request,
      });
    },
    translateTextFirst(request: TranslationRequest) {
      setProgressMessage("첫 page를 번역하는 중입니다.");
      translateTextMutation.mutate({
        ...request,
        translate_scope: "first_page",
        page_index: 0,
      });
    },
    translateUrlFirst(request: UrlTranslationRequest) {
      setViewerMode(request.view_mode);
      translateUrlFirstMutation.mutate({
        ...request,
        translate_scope: "first_page",
        page_index: 0,
      });
    },
    translateTextAll(request: TranslationRequest) {
      setProgressMessage("전체 page를 번역하는 중입니다.");
      translateAllMutation.mutate({
        ...request,
        translate_scope: "all_pages",
      });
    },
    translateUrlAll(request: UrlTranslationRequest) {
      setViewerMode(request.view_mode);
      translateUrlAllMutation.mutate({
        ...request,
        translate_scope: "all_pages",
      });
    },
  };
}

function requestToUiOptions(request: UrlTranslationRequest): TranslationOptions {
  const clientOptions = request.client_options;
  return {
    model: clientOptions?.model ?? "gemma4:26b-a4b-it-q4_K_M",
    promptVersion: clientOptions?.promptVersion,
    style: request.style,
    honorificPolicy: request.honorific_policy,
    think: request.think,
    useGlossary: request.use_glossary,
    useCache: request.use_cache,
    preserveNames: request.preserve_names,
    temperature: request.options.temperature,
    topP: request.options.top_p,
    contextWindow: request.options.num_ctx,
    maxTokens: request.options.num_predict,
  };
}

async function responseFromJob(job: TranslationJob) {
  const fresh = await getTranslationJob(job.jobId, job);
  return {
    job_id: fresh.jobId,
    source_type: fresh.sourceType,
    source_lang: fresh.sourceLang,
    target_lang: fresh.targetLang,
    current_page_index: fresh.currentPageIndex,
    total_pages: fresh.pages.length,
    has_next_page: fresh.currentPageIndex < fresh.pages.length - 1,
    translated_text: fresh.pages[fresh.currentPageIndex]?.translatedText ?? "",
    model: fresh.model,
    prompt_version: fresh.promptVersion,
    style: fresh.options.style,
    elapsed_ms: 0,
    cache_hit: false,
    chunks: [],
  };
}
