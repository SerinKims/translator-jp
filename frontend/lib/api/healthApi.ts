import { apiRequest } from "@/lib/api/client";
import type { HealthResponse } from "@/types/health";

export async function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/health");
}
