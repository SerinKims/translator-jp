"use client"

import { BookOpen, Check, Import, Plus, RefreshCw, X } from "lucide-react"
import { FormEvent, useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import {
  approveGlossaryCandidate,
  createGlossaryTerm,
  deactivateGlossaryTerm,
  importGlossary,
  listGlossary,
  listGlossaryCandidates,
  reactivateGlossaryTerm,
  rejectGlossaryCandidate,
  updateGlossaryTerm,
} from "@/lib/api"
import type { GlossaryTerm, GlossaryTermInput, SourceLang } from "@/lib/types"

const emptyTerm: GlossaryTermInput = {
  source_lang: "ja",
  target_lang: "ko",
  source_term: "",
  target_term: "",
  term_type: "common",
  description: "",
  aliases: [],
  priority: 0,
  is_required: true,
  is_active: true,
}

export function GlossaryManager() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<GlossaryTermInput>(emptyTerm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [aliasText, setAliasText] = useState("")
  const [csvText, setCsvText] = useState("")
  const [message, setMessage] = useState<string | null>(null)
  const [showInactiveTerms, setShowInactiveTerms] = useState(false)

  const glossaryQuery = useQuery({
    queryKey: ["glossary"],
    queryFn: listGlossary,
  })
  const candidatesQuery = useQuery({
    queryKey: ["glossary-candidates"],
    queryFn: () => listGlossaryCandidates("pending"),
  })

  const activeTerms = useMemo(
    () => glossaryQuery.data?.filter((term) => term.is_active) ?? [],
    [glossaryQuery.data],
  )
  const inactiveTerms = useMemo(
    () => glossaryQuery.data?.filter((term) => !term.is_active) ?? [],
    [glossaryQuery.data],
  )

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = { ...form, aliases: parseAliases(aliasText) }
      return editingId
        ? updateGlossaryTerm(editingId, payload)
        : createGlossaryTerm(payload)
    },
    onSuccess: async () => {
      setMessage("용어를 저장했습니다.")
      resetForm()
      await queryClient.invalidateQueries({ queryKey: ["glossary"] })
    },
    onError: (error) => setMessage(error instanceof Error ? error.message : "용어 저장에 실패했습니다."),
  })

  const deactivateMutation = useMutation({
    mutationFn: (termId: number) => deactivateGlossaryTerm(termId),
    onSuccess: async () => {
      setMessage("용어를 비활성화했습니다.")
      await queryClient.invalidateQueries({ queryKey: ["glossary"] })
    },
  })

  const reactivateMutation = useMutation({
    mutationFn: (termId: number) => reactivateGlossaryTerm(termId),
    onSuccess: async () => {
      setMessage("용어를 재활성화했습니다.")
      await queryClient.invalidateQueries({ queryKey: ["glossary"] })
    },
  })

  const importMutation = useMutation({
    mutationFn: importGlossary,
    onSuccess: async (result) => {
      setMessage(`CSV import 완료: ${result.imported}개 추가, ${result.skipped_duplicates}개 중복`)
      setCsvText("")
      await queryClient.invalidateQueries({ queryKey: ["glossary"] })
    },
  })

  const candidateMutation = useMutation({
    mutationFn: async ({
      id,
      action,
    }: {
      id: number
      action: "approve" | "reject"
    }) => (action === "approve" ? approveGlossaryCandidate(id) : rejectGlossaryCandidate(id)),
    onSuccess: async () => {
      setMessage("후보 용어 상태를 변경했습니다.")
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["glossary"] }),
        queryClient.invalidateQueries({ queryKey: ["glossary-candidates"] }),
      ])
    },
  })

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage(null)
    saveMutation.mutate()
  }

  const startEdit = (term: GlossaryTerm) => {
    setEditingId(term.id)
    setForm({
      source_lang: normalizeSource(term.source_lang),
      target_lang: "ko",
      source_term: term.source_term,
      target_term: term.target_term,
      term_type: term.term_type,
      description: term.description ?? "",
      aliases: term.aliases,
      priority: term.priority,
      is_required: term.is_required,
      is_active: term.is_active,
    })
    setAliasText(term.aliases.join(", "))
  }

  const resetForm = () => {
    setEditingId(null)
    setForm(emptyTerm)
    setAliasText("")
  }

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-xl font-medium">
          <BookOpen aria-hidden className="h-5 w-5" />
          용어집 관리
        </h2>
        <Button
          variant="ghost"
          className="min-h-9 px-3"
          onClick={() => {
            glossaryQuery.refetch()
            candidatesQuery.refetch()
          }}
        >
          <RefreshCw aria-hidden className="h-4 w-4" />
          새로고침
        </Button>
      </div>

      <form className="space-y-3 rounded-lg border border-[#d9d9dd] p-3" onSubmit={submit}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Select
            value={form.source_lang}
            onChange={(event) =>
              setForm((value) => ({ ...value, source_lang: event.target.value as SourceLang }))
            }
          >
            <option value="ja">일본어</option>
            <option value="zh-CN">중국어 간체</option>
            <option value="zh-TW">중국어 번체</option>
            <option value="en">영어</option>
          </Select>
          <Input value="한국어" disabled />
          <Input
            value={form.source_term}
            placeholder="원어"
            onChange={(event) =>
              setForm((value) => ({ ...value, source_term: event.target.value }))
            }
          />
          <Input
            value={form.target_term}
            placeholder="번역어"
            onChange={(event) =>
              setForm((value) => ({ ...value, target_term: event.target.value }))
            }
          />
          <Input
            value={form.term_type}
            placeholder="term_type"
            onChange={(event) =>
              setForm((value) => ({ ...value, term_type: event.target.value }))
            }
          />
          <Input
            value={form.priority}
            type="number"
            placeholder="priority"
            onChange={(event) =>
              setForm((value) => ({ ...value, priority: Number(event.target.value) }))
            }
          />
        </div>
        <Input
          value={aliasText}
          placeholder="aliases: 쉼표로 구분"
          onChange={(event) => setAliasText(event.target.value)}
        />
        <Textarea
          value={form.description ?? ""}
          className="min-h-24"
          placeholder="설명"
          onChange={(event) =>
            setForm((value) => ({ ...value, description: event.target.value }))
          }
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_required}
            className="h-4 w-4 accent-[#17171c]"
            onChange={(event) =>
              setForm((value) => ({ ...value, is_required: event.target.checked }))
            }
          />
          필수 용어
        </label>
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={saveMutation.isPending}>
            <Plus aria-hidden className="h-4 w-4" />
            {editingId ? "용어 수정" : "용어 추가"}
          </Button>
          {editingId ? (
            <Button variant="outline" onClick={resetForm}>
              취소
            </Button>
          ) : null}
        </div>
      </form>

      <div className="space-y-2">
        <h3 className="text-sm font-medium">활성 용어</h3>
        {activeTerms.length === 0 ? (
          <p className="text-sm text-[#75758a]">활성 용어가 없습니다.</p>
        ) : null}
        {activeTerms.map((term) => (
          <div
            key={term.id}
            className="rounded-lg border border-[#d9d9dd] bg-white px-3 py-3"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <div className="text-sm font-medium">
                  {term.source_term} → {term.target_term}
                </div>
                <div className="mt-1 text-xs text-[#75758a]">
                  {term.source_lang} / {term.term_type} / priority {term.priority}
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="min-h-8 px-3" onClick={() => startEdit(term)}>
                  수정
                </Button>
                <Button
                  variant="ghost"
                  className="min-h-8 px-3"
                  onClick={() => deactivateMutation.mutate(term.id)}
                >
                  비활성화
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-medium">비활성 용어</h3>
          <Button
            variant="ghost"
            className="min-h-8 px-3"
            onClick={() => setShowInactiveTerms((value) => !value)}
          >
            {showInactiveTerms ? "비활성 용어 숨기기" : `비활성 용어 보기 (${inactiveTerms.length})`}
          </Button>
        </div>
        {showInactiveTerms ? (
          inactiveTerms.length === 0 ? (
            <p className="text-sm text-[#75758a]">비활성 용어가 없습니다.</p>
          ) : (
            inactiveTerms.map((term) => (
              <div
                key={term.id}
                className="rounded-lg border border-[#d9d9dd] bg-[#f7f7f7] px-3 py-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-medium">
                      {term.source_term} → {term.target_term}
                    </div>
                    <div className="mt-1 text-xs text-[#75758a]">
                      {term.source_lang} / {term.term_type} / priority {term.priority}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    className="min-h-8 px-3"
                    disabled={reactivateMutation.isPending}
                    onClick={() => reactivateMutation.mutate(term.id)}
                  >
                    재활성화
                  </Button>
                </div>
              </div>
            ))
          )
        ) : null}
      </div>

      <div className="space-y-3 rounded-lg border border-[#d9d9dd] p-3">
        <h3 className="text-sm font-medium">CSV import</h3>
        <Textarea
          value={csvText}
          className="min-h-28"
          placeholder="source_lang,target_lang,source_term,target_term,term_type,priority,is_required,description,aliases"
          onChange={(event) => setCsvText(event.target.value)}
        />
        <Button
          variant="outline"
          disabled={!csvText.trim() || importMutation.isPending}
          onClick={() => importMutation.mutate(csvText)}
        >
          <Import aria-hidden className="h-4 w-4" />
          CSV import
        </Button>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium">후보 용어</h3>
        {candidatesQuery.data?.length === 0 ? (
          <p className="text-sm text-[#75758a]">승인 대기 후보가 없습니다.</p>
        ) : null}
        {candidatesQuery.data?.map((candidate) => (
          <div key={candidate.id} className="rounded-lg border border-[#d9d9dd] p-3">
            <div className="text-sm font-medium">
              {candidate.source_term} → {candidate.suggested_target_term}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button
                className="min-h-8 px-3"
                onClick={() =>
                  candidateMutation.mutate({ id: candidate.id, action: "approve" })
                }
              >
                <Check aria-hidden className="h-4 w-4" />
                승인
              </Button>
              <Button
                variant="outline"
                className="min-h-8 px-3"
                onClick={() =>
                  candidateMutation.mutate({ id: candidate.id, action: "reject" })
                }
              >
                <X aria-hidden className="h-4 w-4" />
                거절
              </Button>
            </div>
          </div>
        ))}
      </div>

      {message ? <p className="text-sm text-[#003c33]">{message}</p> : null}
    </section>
  )
}

function parseAliases(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizeSource(value: string): SourceLang {
  if (value === "ja" || value === "zh-CN" || value === "zh-TW" || value === "en") {
    return value
  }
  return "ja"
}
