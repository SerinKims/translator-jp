"use client";

import { Pencil, Trash2 } from "lucide-react";
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { GlossaryTerm, GlossaryTermCreateRequest, GlossaryTermType } from "@/types/glossary";

const termTypeLabels: Record<GlossaryTermType, string> = {
  person: "인명",
  place: "지명",
  skill: "기술명",
  proper_noun: "고유명사",
  common: "일반 용어",
};

export function GlossaryManager({
  createTerm,
  deleteTerm,
  terms,
  updateTerm,
}: {
  createTerm: (request: GlossaryTermCreateRequest) => void;
  deleteTerm: (id: number) => void;
  terms: GlossaryTerm[];
  updateTerm: (id: number, request: Partial<GlossaryTermCreateRequest>) => void;
}) {
  const [editingTerm, setEditingTerm] = useState<GlossaryTerm | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<GlossaryTerm | null>(null);
  const [sourceTerm, setSourceTerm] = useState("");
  const [targetTerm, setTargetTerm] = useState("");
  const [termType, setTermType] = useState<GlossaryTermType>("common");
  const [priority, setPriority] = useState(80);

  const startEdit = (term: GlossaryTerm) => {
    setEditingTerm(term);
    setSourceTerm(term.source_term);
    setTargetTerm(term.target_term);
    setTermType(term.term_type);
    setPriority(term.priority);
  };

  const resetForm = () => {
    setEditingTerm(null);
    setSourceTerm("");
    setTargetTerm("");
    setTermType("common");
    setPriority(80);
  };

  const submit = () => {
    if (!sourceTerm.trim() || !targetTerm.trim()) {
      return;
    }

    const request: GlossaryTermCreateRequest = {
      source_lang: "ja",
      target_lang: "ko",
      source_term: sourceTerm.trim(),
      target_term: targetTerm.trim(),
      term_type: termType,
      priority,
      is_required: true,
      is_active: true,
      aliases: [],
      description: null,
    };

    if (editingTerm) {
      updateTerm(editingTerm.id, request);
    } else {
      createTerm(request);
    }
    resetForm();
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>용어집 관리</CardTitle>
            <CardDescription className="mt-2">용어를 추가, 수정, 삭제할 수 있습니다.</CardDescription>
          </div>
          <Badge variant="secondary">{terms.length}개</Badge>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>원문 용어</TableHead>
                <TableHead>한국어 표기</TableHead>
                <TableHead>유형</TableHead>
                <TableHead>우선순위</TableHead>
                <TableHead className="text-right">관리</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {terms.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                    등록된 용어가 없습니다.
                  </TableCell>
                </TableRow>
              ) : (
                terms.map((term) => (
                  <TableRow key={term.id}>
                    <TableCell className="font-medium">{term.source_term}</TableCell>
                    <TableCell>{term.target_term}</TableCell>
                    <TableCell>{termTypeLabels[term.term_type]}</TableCell>
                    <TableCell>{term.priority}</TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button type="button" size="sm" variant="outline" onClick={() => startEdit(term)}>
                          <Pencil className="h-4 w-4" />
                          수정
                        </Button>
                        <Button type="button" size="sm" variant="destructive" onClick={() => setDeleteTarget(term)}>
                          <Trash2 className="h-4 w-4" />
                          삭제
                        </Button>
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
          <CardDescription>우선순위가 높을수록 먼저 적용하는 용도로 사용할 수 있습니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <LabeledField label="원문 용어">
            <Input value={sourceTerm} onChange={(event) => setSourceTerm(event.target.value)} placeholder="예: 夕焼け" />
          </LabeledField>
          <LabeledField label="한국어 표기">
            <Input value={targetTerm} onChange={(event) => setTargetTerm(event.target.value)} placeholder="예: 노을" />
          </LabeledField>
          <LabeledField label="유형">
            <Select value={termType} onValueChange={(value) => setTermType(value as GlossaryTermType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(termTypeLabels).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </LabeledField>
          <LabeledField label="우선순위">
            <Input type="number" value={priority} onChange={(event) => setPriority(Number(event.target.value))} />
          </LabeledField>
          <div className="flex gap-2">
            <Button type="button" onClick={submit}>
              {editingTerm ? "수정 저장" : "용어 추가"}
            </Button>
            {editingTerm && (
              <Button type="button" variant="outline" onClick={resetForm}>
                수정 취소
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>이 용어를 삭제할까요?</AlertDialogTitle>
            <AlertDialogDescription>mock 용어집에서 선택한 항목이 삭제됩니다.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTarget) {
                  deleteTerm(deleteTarget.id);
                }
                setDeleteTarget(null);
              }}
            >
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function LabeledField({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      <span>{label}</span>
      {children}
    </label>
  );
}
