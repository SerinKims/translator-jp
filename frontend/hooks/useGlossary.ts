"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveGlossaryCandidate,
  createGlossaryTerm,
  deleteGlossaryTerm,
  importGlossary,
  listGlossary,
  listGlossaryCandidates,
  permanentlyDeleteGlossaryTerm,
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
  const createTerm = useMutation({
    mutationFn: (request: GlossaryTermCreateRequest) => createGlossaryTerm(request),
    onSuccess: invalidate,
  });
  const updateTerm = useMutation({
    mutationFn: ({ id, request }: { id: number; request: GlossaryTermUpdateRequest }) =>
      updateGlossaryTerm(id, request),
    onSuccess: invalidate,
  });
  const deleteTerm = useMutation({
    mutationFn: deleteGlossaryTerm,
    onSuccess: invalidate,
  });
  const permanentlyDeleteTerm = useMutation({
    mutationFn: permanentlyDeleteGlossaryTerm,
    onSuccess: invalidate,
  });
  const importTerms = useMutation({
    mutationFn: (request: GlossaryImportRequest) => importGlossary(request),
    onSuccess: invalidate,
  });
  const approveCandidate = useMutation({
    mutationFn: ({ id, request }: { id: number; request: GlossaryCandidateApproveRequest }) =>
      approveGlossaryCandidate(id, request),
    onSuccess: invalidate,
  });
  const rejectCandidate = useMutation({
    mutationFn: rejectGlossaryCandidate,
    onSuccess: invalidate,
  });

  return {
    terms: query.data ?? [],
    candidates: candidatesQuery.data ?? [],
    error:
      query.error ??
      candidatesQuery.error ??
      createTerm.error ??
      updateTerm.error ??
      deleteTerm.error ??
      permanentlyDeleteTerm.error ??
      importTerms.error ??
      approveCandidate.error ??
      rejectCandidate.error,
    isLoading: query.isLoading,
    isCandidatesLoading: candidatesQuery.isLoading,
    createTerm,
    updateTerm,
    deleteTerm,
    permanentlyDeleteTerm,
    importTerms,
    approveCandidate,
    rejectCandidate,
  };
}
