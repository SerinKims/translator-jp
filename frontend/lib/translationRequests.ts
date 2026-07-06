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
    style: overrides?.style ?? settings.style,
    honorificPolicy: overrides?.honorificPolicy ?? settings.honorificPolicy,
    think: overrides?.think ?? settings.think,
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
    client_options: input.options,
    text: input.text,
    model_name: input.options.model,
    prompt_version: input.options.promptVersion,
    source_lang: input.sourceLang,
    target_lang: "ko",
    translate_scope: "first_page",
    page_index: 0,
    style: input.options.style,
    honorific_policy: input.options.honorificPolicy,
    preserve_names: input.options.preserveNames,
    use_glossary: input.options.useGlossary,
    use_cache: input.options.useCache,
    stream: false,
    think: input.options.think,
    options: {
      temperature: input.options.temperature,
      top_p: input.options.topP,
      num_ctx: input.options.contextWindow,
      num_predict: input.options.maxTokens,
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
    client_options: job.options,
    model_name: job.options.model,
    prompt_version: job.options.promptVersion,
    source_lang: job.sourceLang,
    target_lang: job.targetLang,
    style: job.options.style,
    honorific_policy: job.options.honorificPolicy,
    preserve_names: job.options.preserveNames,
    use_glossary: job.options.useGlossary,
    use_cache: job.options.useCache,
    stream: false,
    think: job.options.think,
    force: false,
    options: {
      temperature: job.options.temperature,
      top_p: job.options.topP,
      num_ctx: job.options.contextWindow,
      num_predict: job.options.maxTokens,
    },
  };
}
