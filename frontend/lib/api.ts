import type {
  GlossaryCandidate,
  GlossaryImportResponse,
  GlossaryTerm,
  GlossaryTermInput,
  PageTranslateRequest,
  PixivTranslateRequest,
  TranslateRequest,
  TranslationDetailResponse,
  TranslationHistoryItem,
  TranslationResponse,
} from "@/lib/types"

type RequestBody = object | string | undefined
type ApiFetchOptions = Omit<RequestInit, "body"> & { body?: RequestBody }

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const headers = new Headers(options.headers)
  const isStringBody = typeof options.body === "string"
  if (options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", isStringBody ? "text/csv; charset=utf-8" : "application/json")
  }
  let body: BodyInit | undefined
  if (typeof options.body === "string") {
    body = options.body
  } else if (options.body !== undefined) {
    body = JSON.stringify(options.body)
  }

  const response = await fetch(path, {
    ...options,
    headers,
    body,
  })

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function translateText(request: TranslateRequest) {
  return apiFetch<TranslationResponse>("/api/translate", {
    method: "POST",
    body: request,
  })
}

export async function translatePixiv(request: PixivTranslateRequest) {
  return apiFetch<TranslationResponse>("/api/fetch/pixiv/translate", {
    method: "POST",
    body: request,
  })
}

export async function translatePage(
  jobId: number,
  pageIndex: number,
  request: PageTranslateRequest,
) {
  return apiFetch<TranslationResponse>(
    `/api/translations/${jobId}/pages/${pageIndex}/translate`,
    {
      method: "POST",
      body: request,
    },
  )
}

export async function listTranslations(limit = 20) {
  return apiFetch<TranslationHistoryItem[]>(`/api/translations?limit=${limit}`)
}

export async function getTranslationDetail(jobId: number) {
  return apiFetch<TranslationDetailResponse>(`/api/translations/${jobId}`)
}

export const getTranslation = getTranslationDetail

export async function listGlossary() {
  return apiFetch<GlossaryTerm[]>("/api/glossary")
}

export async function createGlossaryTerm(request: GlossaryTermInput) {
  return apiFetch<GlossaryTerm>("/api/glossary", {
    method: "POST",
    body: request,
  })
}

export async function updateGlossaryTerm(
  termId: number,
  request: Partial<GlossaryTermInput>,
) {
  return apiFetch<GlossaryTerm>(`/api/glossary/${termId}`, {
    method: "PATCH",
    body: request,
  })
}

export async function deactivateGlossaryTerm(termId: number) {
  return apiFetch<GlossaryTerm>(`/api/glossary/${termId}`, {
    method: "DELETE",
  })
}

export async function reactivateGlossaryTerm(termId: number) {
  return apiFetch<GlossaryTerm>(`/api/glossary/${termId}`, {
    method: "PATCH",
    body: { is_active: true },
  })
}

export async function importGlossary(text: string) {
  return apiFetch<GlossaryImportResponse>("/api/glossary/import", {
    method: "POST",
    body: { text },
  })
}

export async function listGlossaryCandidates(status = "pending") {
  return apiFetch<GlossaryCandidate[]>(`/api/glossary/candidates?status=${status}`)
}

export async function approveGlossaryCandidate(candidateId: number) {
  return apiFetch<GlossaryCandidate>(
    `/api/glossary/candidates/${candidateId}/approve`,
    {
      method: "POST",
      body: {},
    },
  )
}

export async function rejectGlossaryCandidate(candidateId: number) {
  return apiFetch<GlossaryCandidate>(
    `/api/glossary/candidates/${candidateId}/reject`,
    {
      method: "POST",
      body: {},
    },
  )
}

async function readErrorMessage(response: Response) {
  const fallback = defaultErrorMessage(response.status)
  try {
    const payload = (await response.json()) as unknown
    if (typeof payload === "string") {
      return payload || fallback
    }
    if (payload && typeof payload === "object") {
      const detail = "detail" in payload ? payload.detail : undefined
      if (typeof detail === "string") {
        return detail
      }
      if (Array.isArray(detail) && detail.length > 0) {
        return "요청 형식을 확인해주세요."
      }
      const message = "message" in payload ? payload.message : undefined
      if (typeof message === "string") {
        return message
      }
    }
  } catch {
    return fallback
  }
  return fallback
}

function defaultErrorMessage(status: number) {
  if (status === 404) {
    return "요청한 데이터를 찾을 수 없습니다."
  }
  if (status === 408 || status === 504) {
    return "번역 시간이 너무 오래 걸렸습니다. 입력 문장을 줄이거나 다시 시도해주세요."
  }
  if (status >= 500) {
    return "Ollama 서버에 연결할 수 없습니다. 로컬에서 Ollama가 실행 중인지 확인해주세요."
  }
  return "요청을 처리하지 못했습니다. 입력값을 확인하고 다시 시도해주세요."
}
