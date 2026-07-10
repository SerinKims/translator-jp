"use client";

import { useMutation } from "@tanstack/react-query";

import { clearTranslationCache } from "@/lib/api/cacheApi";

export function useTranslationCache() {
  return {
    clearCache: useMutation({
      mutationFn: clearTranslationCache,
    }),
  };
}
