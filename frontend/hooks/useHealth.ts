"use client";

import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/lib/api/healthApi";
import type { HealthState } from "@/types/health";

export function useHealth() {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: Number.POSITIVE_INFINITY,
    retry: false,
    refetchOnWindowFocus: false,
  });

  let state: HealthState = "checking";
  if (query.error) {
    state = "unreachable";
  } else if (query.data) {
    state =
      query.data.status === "ok" &&
      query.data.ollama === "ok" &&
      query.data.database === "ok" &&
      query.data.model !== "not_found"
        ? "healthy"
        : "degraded";
  }

  return {
    error: query.error,
    health: query.data,
    isFetching: query.isFetching,
    refresh: query.refetch,
    state,
  };
}
