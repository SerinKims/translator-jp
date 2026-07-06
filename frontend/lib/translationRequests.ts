import type {
  ModelSettings,
  PageTranslateRequest,
  SourceLanguage,
  TranslationJob,
  TranslationOptions,
  TranslationRequest,
  UrlTranslationRequest,
  ViewerMode,
} from "@/types/translation";

export function createOptionsFromSettings(settings: ModelSettings, overrides?: Partial<TranslationOptions>): TranslationOptions {
  return {
    model: overrides?.model ?? settings.defaultModel,
    promptVersion: overrides?.promptVersion ?? settings.promptVersion,
    useGlossary: overrides?.useGlossary ?? true,
    useCache: overrides?.useCache ?? true,
    preserveNames: overrides?.preserveNames ?? true,
    temperature: overrides?.temperature ?? settings.temperature,
    topP: overrides?.topP ?? settings.topP,
    contextWindow: overrides?.contextWindow ?? settings.contextWindow,
    maxTokens: overrides?.maxTokens ?? settings.maxTokens,
  };
}

export function createTranslationRequest(input: {
  text: string;
  sourceLang: SourceLanguage;
  options: TranslationOptions;
}): TranslationRequest {
  return {
    text: input.text,
    source_lang: input.sourceLang,
    target_lang: "ko",
    translate_scope: "first_page",
    page_index: 0,
    style: "webnovel",
    honorific_policy: "preserve",
    preserve_names: input.options.preserveNames,
    use_glossary: input.options.useGlossary,
    use_cache: input.options.useCache,
    stream: false,
    think: false,
    options: {
      model: input.options.model,
      prompt_version: input.options.promptVersion,
      temperature: input.options.temperature,
      top_p: input.options.topP,
      context_window: input.options.contextWindow,
      max_tokens: input.options.maxTokens,
    },
  };
}

export function createUrlTranslationRequest(input: {
  url: string;
  sourceLang: SourceLanguage;
  options: TranslationOptions;
  viewerMode: ViewerMode;
}): UrlTranslationRequest {
  const request = createTranslationRequest({
    text: "",
    sourceLang: input.sourceLang,
    options: input.options,
  });

  return {
    ...request,
    url: input.url,
    view_mode: input.viewerMode,
  };
}

export function createPageTranslateRequest(job: TranslationJob): PageTranslateRequest {
  return {
    source_lang: job.sourceLang,
    target_lang: job.targetLang,
    style: "webnovel",
    honorific_policy: "preserve",
    preserve_names: job.options.preserveNames,
    use_glossary: job.options.useGlossary,
    use_cache: job.options.useCache,
    stream: false,
    think: false,
    force: false,
    options: {
      model: job.options.model,
      prompt_version: job.options.promptVersion,
      temperature: job.options.temperature,
      top_p: job.options.topP,
      context_window: job.options.contextWindow,
      max_tokens: job.options.maxTokens,
    },
  };
}
