import { apiRequest } from "@/lib/api/client";
import type { PixivFetchRequest, PixivFetchResponse, PixivTranslateRequest, PixivTranslateResponse } from "@/types/source";

export async function fetchPixivSource(request: PixivFetchRequest): Promise<PixivFetchResponse> {
  return apiRequest<PixivFetchResponse>("/api/fetch/pixiv", {
    method: "POST",
    body: JSON.stringify({
      ...request,
      translate_after_fetch: request.translate_after_fetch ?? false,
    }),
  });
}

export async function fetchAndTranslatePixiv(request: PixivTranslateRequest): Promise<PixivTranslateResponse> {
  return apiRequest<PixivTranslateResponse>("/api/fetch/pixiv/translate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
