import { apiRequest } from "@/lib/api/client";
import type {
  GlossaryCandidate,
  GlossaryCandidateApproveRequest,
  GlossaryCandidateCreateRequest,
  GlossaryImportRequest,
  GlossaryImportResponse,
  GlossaryTerm,
  GlossaryTermCreateRequest,
  GlossaryTermUpdateRequest,
} from "@/types/glossary";

export async function listGlossary(): Promise<GlossaryTerm[]> {
  const terms = await apiRequest<GlossaryTerm[]>("/api/glossary");
  return terms.slice().sort((a, b) => b.priority - a.priority);
}

export async function createGlossaryTerm(request: GlossaryTermCreateRequest): Promise<GlossaryTerm> {
  return apiRequest<GlossaryTerm>("/api/glossary", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function updateGlossaryTerm(id: number, request: GlossaryTermUpdateRequest): Promise<GlossaryTerm> {
  return apiRequest<GlossaryTerm>(`/api/glossary/${id}`, {
    method: "PATCH",
    body: JSON.stringify(request),
  });
}

export async function deleteGlossaryTerm(id: number): Promise<GlossaryTerm> {
  return apiRequest<GlossaryTerm>(`/api/glossary/${id}`, {
    method: "DELETE",
  });
}

export async function permanentlyDeleteGlossaryTerm(id: number): Promise<void> {
  return apiRequest<void>(`/api/glossary/${id}/permanent`, {
    method: "DELETE",
  });
}

export async function importGlossary(request: GlossaryImportRequest): Promise<GlossaryImportResponse> {
  return apiRequest<GlossaryImportResponse>("/api/glossary/import", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function listGlossaryCandidates(status?: string): Promise<GlossaryCandidate[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest<GlossaryCandidate[]>(`/api/glossary/candidates${query}`);
}

export async function createGlossaryCandidate(
  request: GlossaryCandidateCreateRequest,
): Promise<GlossaryCandidate> {
  return apiRequest<GlossaryCandidate>("/api/glossary/candidates", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function approveGlossaryCandidate(
  id: number,
  request: GlossaryCandidateApproveRequest,
): Promise<GlossaryCandidate> {
  return apiRequest<GlossaryCandidate>(`/api/glossary/candidates/${id}/approve`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function rejectGlossaryCandidate(id: number): Promise<GlossaryCandidate> {
  return apiRequest<GlossaryCandidate>(`/api/glossary/candidates/${id}/reject`, {
    method: "POST",
  });
}
