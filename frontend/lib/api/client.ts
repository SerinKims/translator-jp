export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type JsonPrimitive = string | number | boolean | null;
export type JsonRecord = Record<string, JsonPrimitive | JsonPrimitive[]>;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

export async function apiRequest<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  if (!API_BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL 환경변수가 설정되지 않았습니다.");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(formatErrorMessage(detail, response.status), response.status, detail);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "알 수 없는 오류가 발생했습니다.";
}

async function readErrorDetail(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function formatErrorMessage(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (isRecord(detail)) {
    const value = detail.detail;
    if (typeof value === "string" && value.trim()) {
      return value;
    }
    if (Array.isArray(value)) {
      return value.map(formatValidationIssue).join("\n");
    }
  }
  return `API 요청에 실패했습니다. (HTTP ${status})`;
}

function formatValidationIssue(issue: unknown): string {
  if (!isRecord(issue)) {
    return "요청 값이 올바르지 않습니다.";
  }
  const location = Array.isArray(issue.loc) ? issue.loc.join(".") : "request";
  const message = typeof issue.msg === "string" ? issue.msg : "요청 값이 올바르지 않습니다.";
  return `${location}: ${message}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
