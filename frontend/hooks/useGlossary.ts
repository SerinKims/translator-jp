"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveGlossaryCandidate,
  createGlossaryTerm,
  deleteGlossaryTerm,
  importGlossary,
  listGlossary,
  listGlossaryCandidates,
  rejectGlossaryCandidate,
  updateGlossaryTerm,
} from "@/lib/api/glossaryApi";
import type {
  GlossaryCandidateApproveRequest,
  GlossaryImportRequest,
  GlossaryTermCreateRequest,
  GlossaryTermUpdateRequest,
} from "@/types/glossary";

export function useGlossary() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["glossary"],
    queryFn: listGlossary,
  });
  const candidatesQuery = useQuery({
    queryKey: ["glossary", "candidates"],
    queryFn: () => listGlossaryCandidates("pending"),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["glossary"] });

  return {
    terms: query.data ?? [],
    candidates: candidatesQuery.data ?? [],
    error: query.error,
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
    importTerms: useMutation({
      mutationFn: (request: GlossaryImportRequest) => importGlossary(request),
      onSuccess: invalidate,
    }),
    approveCandidate: useMutation({
      mutationFn: ({ id, request }: { id: number; request: GlossaryCandidateApproveRequest }) =>
        approveGlossaryCandidate(id, request),
      onSuccess: invalidate,
    }),
    rejectCandidate: useMutation({
      mutationFn: rejectGlossaryCandidate,
      onSuccess: invalidate,
    }),
  };
}
