"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { clearHistory, deleteHistory, listHistory } from "@/lib/api/historyApi";

export function useTranslationHistory() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["history"],
    queryFn: listHistory,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["history"] });

  return {
    histories: query.data ?? [],
    isLoading: query.isLoading,
    deleteHistory: useMutation({
      mutationFn: deleteHistory,
      onSuccess: invalidate,
    }),
    clearHistory: useMutation({
      mutationFn: clearHistory,
      onSuccess: invalidate,
    }),
  };
}
