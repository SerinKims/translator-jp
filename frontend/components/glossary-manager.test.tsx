import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { GlossaryManager } from "@/components/glossary-manager"
import {
  listGlossary,
  listGlossaryCandidates,
  reactivateGlossaryTerm,
} from "@/lib/api"
import type { GlossaryTerm } from "@/lib/types"

vi.mock("@/lib/api", () => ({
  approveGlossaryCandidate: vi.fn(),
  createGlossaryTerm: vi.fn(),
  deactivateGlossaryTerm: vi.fn(),
  importGlossary: vi.fn(),
  listGlossary: vi.fn(),
  listGlossaryCandidates: vi.fn(),
  reactivateGlossaryTerm: vi.fn(),
  rejectGlossaryCandidate: vi.fn(),
  updateGlossaryTerm: vi.fn(),
}))

const terms: GlossaryTerm[] = [
  {
    id: 1,
    source_lang: "ja",
    target_lang: "ko",
    source_term: "魔王",
    target_term: "마왕",
    term_type: "character",
    description: null,
    aliases: [],
    priority: 10,
    is_required: true,
    is_active: true,
    created_at: "2026-07-02T00:00:00",
    updated_at: "2026-07-02T00:00:00",
  },
  {
    id: 2,
    source_lang: "ja",
    target_lang: "ko",
    source_term: "王都",
    target_term: "왕도",
    term_type: "place",
    description: null,
    aliases: [],
    priority: 5,
    is_required: true,
    is_active: false,
    created_at: "2026-07-02T00:00:00",
    updated_at: "2026-07-02T00:00:00",
  },
]

describe("GlossaryManager", () => {
  beforeEach(() => {
    vi.mocked(listGlossary).mockResolvedValue(terms)
    vi.mocked(listGlossaryCandidates).mockResolvedValue([])
    vi.mocked(reactivateGlossaryTerm).mockResolvedValue({
      ...terms[1],
      is_active: true,
    })
  })

  it("shows inactive terms on demand and reactivates a term", async () => {
    renderGlossaryManager()

    expect(await screen.findByText("魔王 → 마왕")).toBeInTheDocument()
    expect(screen.queryByText("王都 → 왕도")).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "비활성 용어 보기 (1)" }))

    expect(await screen.findByText("王都 → 왕도")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "재활성화" }))

    await waitFor(() => {
      expect(reactivateGlossaryTerm).toHaveBeenCalledWith(2)
    })
  })
})

function renderGlossaryManager() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <GlossaryManager />
    </QueryClientProvider>,
  )
}
