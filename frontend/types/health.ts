export interface HealthResponse {
  status: string;
  ollama: string;
  database: string;
  model: string;
  message?: string;
}

export type HealthState = "checking" | "healthy" | "degraded" | "unreachable";
