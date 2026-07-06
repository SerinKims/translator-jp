"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createGlossaryTerm,
  deleteGlossaryTerm,
  listGlossary,
  updateGlossaryTerm,
} from "@/lib/api/glossaryApi";
import type { GlossaryTermCreateRequest, GlossaryTermUpdateRequest } from "@/types/glossary";

export function useGlossary() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["glossary"],
    queryFn: listGlossary,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["glossary"] });

  return {
    terms: query.data ?? [],
    isLoading: query.isLoading,
    createTerm: useMutation({
      mutationFn: (request: GlossaryTermCreateRequest) => createGlossaryTerm(request),
      onSuccess: invalidate,
    }),
    updateTerm: useMutation({
      mutationFn: ({ id, request }: { id: number; request: GlossaryTermUpdateRequest }) => updateGlossaryTerm(id, request),
      onSuccess: invalidate,
    }),
    deleteTerm: useMutation({
      mutationFn: deleteGlossaryTerm,
      onSuccess: invalidate,
    }),
  };
}
