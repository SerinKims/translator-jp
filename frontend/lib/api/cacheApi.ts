import { apiRequest } from "@/lib/api/client";

export async function clearTranslationCache(): Promise<void> {
  await apiRequest<void>("/api/cache/translations", { method: "DELETE" });
}
