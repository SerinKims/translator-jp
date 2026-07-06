"use client";

import { useMutation } from "@tanstack/react-query";

import { fetchPixivSource } from "@/lib/api/sourceApi";
import type { PixivFetchRequest } from "@/types/source";

export function useSource() {
  const fetchSource = useMutation({
    mutationFn: (request: PixivFetchRequest) => fetchPixivSource(request),
  });

  return {
    fetchSource,
  };
}
