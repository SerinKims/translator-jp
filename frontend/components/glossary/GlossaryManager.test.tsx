import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { GlossaryManager } from "@/components/glossary/GlossaryManager";
import { ApiError } from "@/lib/api/client";
import type {
  GlossaryImportRequest,
  GlossaryImportResponse,
  GlossaryTerm,
} from "@/types/glossary";

type ImportOptions = {
  onSuccess: (result: GlossaryImportResponse) => void;
};

const existingTerm: GlossaryTerm = {
  id: 1,
  glossary_set_id: null,
  source_lang: "ja",
  target_lang: "ko",
  source_term: "王都",
  target_term: "왕도",
  term_type: "place",
  description: null,
  aliases: [],
  priority: 80,
  is_required: true,
  is_case_sensitive: false,
  is_active: true,
  created_at: "2026-07-09T00:00:00",
  updated_at: "2026-07-09T00:00:00",
};

function renderManager({
  importTerms = vi.fn(),
  error = null,
  isImporting = false,
  terms = [],
}: {
  importTerms?: (request: GlossaryImportRequest, options: ImportOptions) => void;
  error?: unknown;
  isImporting?: boolean;
  terms?: GlossaryTerm[];
} = {}) {
  render(
    <GlossaryManager
      createTerm={vi.fn()}
      deleteTerm={vi.fn()}
      error={error}
      importTerms={importTerms}
      isImporting={isImporting}
      isLoading={false}
      isMutating={isImporting}
      permanentlyDeleteTerm={vi.fn()}
      terms={terms}
      updateTerm={vi.fn()}
    />,
  );
}

function csvFile(text: string, readText: () => Promise<string> = () => Promise.resolve(text)): File {
  const file = new File([text], "glossary.csv", { type: "text/csv" });
  Object.defineProperty(file, "text", {
    configurable: true,
    value: vi.fn().mockImplementation(readText),
  });
  return file;
}

describe("GlossaryManager CSV import", () => {
  it("sends the selected CSV text and renders the detailed result", async () => {
    const user = userEvent.setup();
    const csvText = "source_lang,target_lang,source_term,target_term\nja,ko,王都,왕도\n";
    const importTerms = vi.fn(
      (_request: GlossaryImportRequest, options: ImportOptions) => {
        options.onSuccess({
          imported: 2,
          skipped_duplicates: 1,
          conflicts: [
            {
              row: 4,
              source_lang: "ja",
              target_lang: "ko",
              source_term: "王都",
              target_term: "수도",
              message: "같은 원어에 다른 번역어가 이미 등록되어 있습니다.",
            },
          ],
        });
      },
    );
    renderManager({ importTerms });

    await user.upload(screen.getByLabelText("CSV 파일 선택"), csvFile(csvText));

    await waitFor(() => {
      expect(importTerms).toHaveBeenCalledWith(
        { text: csvText },
        expect.objectContaining({ onSuccess: expect.any(Function) }),
      );
    });
    expect(screen.getByText("2개 등록")).toBeInTheDocument();
    expect(screen.getByText("1개 중복")).toBeInTheDocument();
    expect(screen.getByText("1개 충돌")).toBeInTheDocument();
    expect(screen.getByText("4행")).toBeInTheDocument();
    expect(screen.getByText("王都 → 수도")).toBeInTheDocument();
    expect(screen.getByText("같은 원어에 다른 번역어가 이미 등록되어 있습니다.")).toBeInTheDocument();
  });

  it("rejects an empty CSV before calling the import mutation", async () => {
    const user = userEvent.setup();
    const importTerms = vi.fn();
    renderManager({ importTerms });

    await user.upload(screen.getByLabelText("CSV 파일 선택"), csvFile(" \n"));

    expect(await screen.findByText("CSV 파일 내용이 비어 있습니다.")).toBeInTheDocument();
    expect(importTerms).not.toHaveBeenCalled();
  });

  it("shows a Korean error when the browser cannot read the file", async () => {
    const user = userEvent.setup();
    const importTerms = vi.fn();
    renderManager({
      importTerms,
    });

    await user.upload(
      screen.getByLabelText("CSV 파일 선택"),
      csvFile("", () => Promise.reject(new Error("read failed"))),
    );

    expect(await screen.findByText("CSV 파일을 읽지 못했습니다. UTF-8 형식인지 확인해주세요.")).toBeInTheDocument();
    expect(importTerms).not.toHaveBeenCalled();
  });

  it("renders an API import error supplied by the mutation", () => {
    renderManager({
      error: new ApiError("CSV의 priority 값은 정수여야 합니다.", 400),
    });

    expect(screen.getByText("CSV의 priority 값은 정수여야 합니다.")).toBeInTheDocument();
  });

  it("allows the same file to be selected again", async () => {
    const user = userEvent.setup();
    const importTerms = vi.fn();
    const file = csvFile("source_term,target_term\n王都,왕도\n");
    renderManager({ importTerms });
    const input = screen.getByLabelText("CSV 파일 선택");

    await user.upload(input, file);
    await user.upload(input, file);

    expect(importTerms).toHaveBeenCalledTimes(2);
  });

  it("disables import and term controls while importing", () => {
    renderManager({ isImporting: true, terms: [existingTerm] });

    expect(screen.getByRole("button", { name: "가져오는 중..." })).toBeDisabled();
    expect(screen.getByLabelText("CSV 파일 선택")).toBeDisabled();
    expect(screen.getByRole("button", { name: "수정" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "비활성화" })).toBeDisabled();
  });
});
