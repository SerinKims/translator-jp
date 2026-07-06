import { delay, readStorage, writeStorage } from "@/lib/api/storage";
import type { GlossaryTerm, GlossaryTermCreateRequest, GlossaryTermUpdateRequest } from "@/types/glossary";

const GLOSSARY_STORAGE_KEY = "translator-next-mock-glossary-v1";

const seedGlossary: GlossaryTerm[] = [
  createSeedTerm(1, "夕焼け", "노을", "common", 80),
  createSeedTerm(2, "Phainon", "파이논", "person", 100),
  createSeedTerm(3, "鐘の音", "종소리", "proper_noun", 90),
];

export async function listGlossary(): Promise<GlossaryTerm[]> {
  await delay(100);
  return getGlossary().sort((a, b) => b.priority - a.priority);
}

export async function createGlossaryTerm(request: GlossaryTermCreateRequest): Promise<GlossaryTerm> {
  await delay(100);
  const now = new Date().toISOString();
  const term: GlossaryTerm = {
    id: Date.now(),
    description: request.description ?? null,
    aliases: request.aliases ?? [],
    created_at: now,
    updated_at: now,
    ...request,
  };
  saveGlossary([...getGlossary(), term]);
  return term;
}

export async function updateGlossaryTerm(id: number, request: GlossaryTermUpdateRequest): Promise<GlossaryTerm> {
  await delay(100);
  const terms = getGlossary();
  const target = terms.find((term) => term.id === id);
  if (!target) {
    throw new Error("용어를 찾을 수 없습니다.");
  }

  const updated: GlossaryTerm = {
    ...target,
    ...request,
    aliases: request.aliases ?? target.aliases,
    description: request.description ?? target.description,
    updated_at: new Date().toISOString(),
  };
  saveGlossary(terms.map((term) => (term.id === id ? updated : term)));
  return updated;
}

export async function deleteGlossaryTerm(id: number) {
  await delay(100);
  saveGlossary(getGlossary().filter((term) => term.id !== id));
}

function getGlossary() {
  return readStorage<GlossaryTerm[]>(GLOSSARY_STORAGE_KEY, seedGlossary);
}

function saveGlossary(terms: GlossaryTerm[]) {
  writeStorage(GLOSSARY_STORAGE_KEY, terms);
}

function createSeedTerm(id: number, source: string, target: string, termType: GlossaryTerm["term_type"], priority: number): GlossaryTerm {
  const now = new Date().toISOString();
  return {
    id,
    source_lang: "ja",
    target_lang: "ko",
    source_term: source,
    target_term: target,
    term_type: termType,
    description: null,
    aliases: [],
    priority,
    is_required: true,
    is_active: true,
    created_at: now,
    updated_at: now,
  };
}
