"use client";

import type { ReactNode } from "react";
import { Eye, EyeOff, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/api/client";
import type {
  GlossarySourceLanguage,
  GlossaryTerm,
  GlossaryTermCreateRequest,
  GlossaryTermType,
} from "@/types/glossary";

const sourceLanguageLabels: Record<GlossarySourceLanguage, string> = {
  ja: "일본어",
  "zh-CN": "중국어 간체",
  "zh-TW": "중국어 번체",
  en: "영어",
};

const termTypeLabels: Record<GlossaryTermType, string> = {
  common: "일반 용어",
  person: "인명",
  place: "지명",
  title: "호칭/직함",
  skill: "기술명",
  organization: "조직명",
  honorific: "경칭",
  proper_noun: "고유명사",
};

const sourceLanguageOptions = Object.keys(sourceLanguageLabels) as GlossarySourceLanguage[];
const termTypeOptions = Object.keys(termTypeLabels) as GlossaryTermType[];

export function GlossaryManager({
  createTerm,
  deleteTerm,
  error,
  isLoading,
  isMutating,
  permanentlyDeleteTerm,
  terms,
  updateTerm,
}: {
  createTerm: (request: GlossaryTermCreateRequest) => void;
  deleteTerm: (id: number) => void;
  error: unknown;
  isLoading: boolean;
  isMutating: boolean;
  permanentlyDeleteTerm: (id: number, onSuccess: () => void) => void;
  terms: GlossaryTerm[];
  updateTerm: (id: number, request: Partial<GlossaryTermCreateRequest>) => void;
}) {
  const [editingTerm, setEditingTerm] = useState<GlossaryTerm | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<GlossaryTerm | null>(null);
  const [permanentDeleteTarget, setPermanentDeleteTarget] = useState<GlossaryTerm | null>(null);
  const [sourceLang, setSourceLang] = useState<GlossarySourceLanguage>("ja");
  const [sourceTerm, setSourceTerm] = useState("");
  const [targetTerm, setTargetTerm] = useState("");
  const [termType, setTermType] = useState<GlossaryTermType>("common");
  const [description, setDescription] = useState("");
  const [aliasesText, setAliasesText] = useState("");
  const [priority, setPriority] = useState(80);
  const [isRequired, setIsRequired] = useState(true);
  const [isCaseSensitive, setIsCaseSensitive] = useState(false);

  const sortedTerms = terms
    .slice()
    .sort((a, b) => b.priority - a.priority || a.source_term.localeCompare(b.source_term));

  const startEdit = (term: GlossaryTerm) => {
    setEditingTerm(term);
    setSourceLang(term.source_lang);
    setSourceTerm(term.source_term);
    setTargetTerm(term.target_term);
    setTermType(term.term_type);
    setDescription(term.description ?? "");
    setAliasesText(term.aliases.join("\n"));
    setPriority(term.priority);
    setIsRequired(term.is_required);
    setIsCaseSensitive(term.is_case_sensitive);
  };

  const resetForm = () => {
    setEditingTerm(null);
    setSourceLang("ja");
    setSourceTerm("");
    setTargetTerm("");
    setTermType("common");
    setDescription("");
    setAliasesText("");
    setPriority(80);
    setIsRequired(true);
    setIsCaseSensitive(false);
  };

  const submit = () => {
    const cleanedSourceTerm = sourceTerm.trim();
    const cleanedTargetTerm = targetTerm.trim();
    if (!cleanedSourceTerm || !cleanedTargetTerm) {
      return;
    }

    const request: GlossaryTermCreateRequest = {
      glossary_set_id: editingTerm?.glossary_set_id ?? null,
      source_lang: sourceLang,
      target_lang: "ko",
      source_term: cleanedSourceTerm,
      target_term: cleanedTargetTerm,
      term_type: termType,
      description: description.trim() || null,
      aliases: parseAliases(aliasesText),
      priority,
      is_required: isRequired,
      is_case_sensitive: isCaseSensitive,
      is_active: editingTerm?.is_active ?? true,
    };

    if (editingTerm) {
      updateTerm(editingTerm.id, request);
    } else {
      createTerm(request);
    }
    resetForm();
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>용어집 관리</CardTitle>
          </div>
          <Badge variant="secondary">{terms.length}개</Badge>
        </CardHeader>
        <CardContent className="space-y-3">
          {error ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {getErrorMessage(error)}
            </div>
          ) : null}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>언어</TableHead>
                <TableHead>원문 용어</TableHead>
                <TableHead>한국어 표기</TableHead>
                <TableHead>유형</TableHead>
                <TableHead>별칭</TableHead>
                <TableHead>우선순위</TableHead>
                <TableHead>상태</TableHead>
                <TableHead className="text-right">관리</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <EmptyRow>용어집을 불러오는 중입니다.</EmptyRow>
              ) : sortedTerms.length === 0 ? (
                <EmptyRow>등록된 용어가 없습니다.</EmptyRow>
              ) : (
                sortedTerms.map((term) => (
                  <TableRow key={term.id} className={!term.is_active ? "opacity-60" : undefined}>
                    <TableCell>{sourceLanguageLabels[term.source_lang] ?? term.source_lang}</TableCell>
                    <TableCell className="font-medium">{term.source_term}</TableCell>
                    <TableCell>{term.target_term}</TableCell>
                    <TableCell>{termTypeLabels[term.term_type] ?? term.term_type}</TableCell>
                    <TableCell>{term.aliases.length > 0 ? term.aliases.join(", ") : "-"}</TableCell>
                    <TableCell>{term.priority}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        <Badge variant={term.is_active ? "success" : "secondary"}>
                          {term.is_active ? "활성" : "비활성"}
                        </Badge>
                        {term.is_required ? <Badge variant="secondary">필수</Badge> : null}
                        {term.is_case_sensitive ? <Badge variant="outline">대소문자</Badge> : null}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button type="button" size="sm" variant="outline" onClick={() => startEdit(term)} disabled={isMutating}>
                          <Pencil className="h-4 w-4" />
                          수정
                        </Button>
                        {term.is_active ? (
                          <Button type="button" size="sm" variant="outline" onClick={() => setDeactivateTarget(term)} disabled={isMutating}>
                            <EyeOff className="h-4 w-4" />
                            비활성화
                          </Button>
                        ) : (
                          <>
                            <Button type="button" size="sm" variant="outline" onClick={() => updateTerm(term.id, { is_active: true })} disabled={isMutating}>
                              <Eye className="h-4 w-4" />
                              활성화
                            </Button>
                            <Button type="button" size="sm" variant="destructive" onClick={() => setPermanentDeleteTarget(term)} disabled={isMutating}>
                              <Trash2 className="h-4 w-4" />
                              영구 삭제
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{editingTerm ? "용어 수정" : "용어 추가"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <LabeledField label="원문 언어">
            <Select value={sourceLang} onValueChange={(value) => setSourceLang(value as GlossarySourceLanguage)} disabled={isMutating}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {sourceLanguageOptions.map((value) => (
                  <SelectItem key={value} value={value}>
                    {sourceLanguageLabels[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </LabeledField>
          <LabeledField label="번역 언어">
            <Select value="ko" disabled>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ko">한국어</SelectItem>
              </SelectContent>
            </Select>
          </LabeledField>
          <LabeledField label="원문 용어">
            <Input value={sourceTerm} onChange={(event) => setSourceTerm(event.target.value)} placeholder="魔王" disabled={isMutating} />
          </LabeledField>
          <LabeledField label="한국어 표기">
            <Input value={targetTerm} onChange={(event) => setTargetTerm(event.target.value)} placeholder="마왕" disabled={isMutating} />
          </LabeledField>
          <LabeledField label="유형">
            <Select value={termType} onValueChange={(value) => setTermType(value as GlossaryTermType)} disabled={isMutating}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {termTypeOptions.map((value) => (
                  <SelectItem key={value} value={value}>
                    {termTypeLabels[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </LabeledField>
          <LabeledField label="별칭">
            <Textarea value={aliasesText} onChange={(event) => setAliasesText(event.target.value)} placeholder="魔王様&#10;まおう" disabled={isMutating} />
          </LabeledField>
          <LabeledField label="설명">
            <Textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="판타지 직함" disabled={isMutating} />
          </LabeledField>
          <LabeledField label="우선순위">
            <Input type="number" value={priority} onChange={(event) => setPriority(Number(event.target.value))} disabled={isMutating} />
          </LabeledField>
          <ToggleField label="필수 적용" checked={isRequired} onCheckedChange={setIsRequired} disabled={isMutating} />
          <ToggleField label="대소문자 구분" checked={isCaseSensitive} onCheckedChange={setIsCaseSensitive} disabled={isMutating} />
          <div className="flex gap-2">
            <Button type="button" onClick={submit} disabled={isMutating || !sourceTerm.trim() || !targetTerm.trim()}>
              {editingTerm ? "수정 저장" : "용어 추가"}
            </Button>
            {editingTerm ? (
              <Button type="button" variant="outline" onClick={resetForm} disabled={isMutating}>
                취소
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <AlertDialog open={Boolean(deactivateTarget)} onOpenChange={(open) => !open && setDeactivateTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>용어를 비활성화할까요?</AlertDialogTitle>
            <AlertDialogDescription>번역에는 더 이상 사용되지 않고 목록에는 남습니다.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deactivateTarget) {
                  deleteTerm(deactivateTarget.id);
                }
                setDeactivateTarget(null);
              }}
            >
              비활성화
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={Boolean(permanentDeleteTarget)}
        onOpenChange={(open) => !open && setPermanentDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>용어를 영구 삭제할까요?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{permanentDeleteTarget?.source_term}&quot; 용어가 DB에서 완전히 삭제됩니다.
              이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isMutating}>취소</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isMutating}
              onClick={() => {
                if (permanentDeleteTarget) {
                  const targetId = permanentDeleteTarget.id;
                  permanentlyDeleteTerm(targetId, () => {
                    if (editingTerm?.id === targetId) {
                      resetForm();
                    }
                  });
                }
                setPermanentDeleteTarget(null);
              }}
            >
              영구 삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function EmptyRow({ children }: { children: ReactNode }) {
  return (
    <TableRow>
      <TableCell colSpan={8} className="py-10 text-center text-muted-foreground">
        {children}
      </TableCell>
    </TableRow>
  );
}

function LabeledField({ children, label }: { children: ReactNode; label: string }) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      <span>{label}</span>
      {children}
    </label>
  );
}

function ToggleField({
  checked,
  disabled,
  label,
  onCheckedChange,
}: {
  checked: boolean;
  disabled: boolean;
  label: string;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between rounded-md border border-input px-3 py-2 text-sm font-medium">
      <span>{label}</span>
      <Switch checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} />
    </label>
  );
}

function parseAliases(value: string): string[] {
  return value
    .split(/[\n,|]/)
    .map((alias) => alias.trim())
    .filter(Boolean);
}
