import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MODEL_SETTINGS_STORAGE_KEY, ModelSettings } from "@/components/settings/ModelSettings";
import { DEFAULT_MODEL_SETTINGS } from "@/types/translation";

describe("ModelSettings", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("saves a custom model name and persists it to localStorage", async () => {
    const user = userEvent.setup();
    const onSettingsChange = vi.fn();
    render(<ModelSettings settings={DEFAULT_MODEL_SETTINGS} onSettingsChange={onSettingsChange} />);

    const modelInput = await screen.findByLabelText("모델명");
    await waitFor(() => expect(modelInput).toHaveValue(DEFAULT_MODEL_SETTINGS.defaultModel));
    await user.clear(modelInput);
    await user.type(modelInput, "  llama3.1:8b  ");
    await user.click(screen.getByRole("button", { name: "저장" }));

    expect(onSettingsChange).toHaveBeenCalledWith({
      ...DEFAULT_MODEL_SETTINGS,
      defaultModel: "llama3.1:8b",
    });
    expect(JSON.parse(window.localStorage.getItem(MODEL_SETTINGS_STORAGE_KEY) ?? "{}")).toMatchObject({
      defaultModel: "llama3.1:8b",
    });
  });

  it("keeps preset model suggestions on the model input", async () => {
    render(<ModelSettings settings={DEFAULT_MODEL_SETTINGS} onSettingsChange={vi.fn()} />);

    const modelInput = await screen.findByLabelText("모델명");
    expect(modelInput).toHaveAttribute("list", "ollama-model-presets");

    const presetList = document.getElementById("ollama-model-presets");
    expect(presetList).not.toBeNull();
    expect(Array.from(presetList?.querySelectorAll("option") ?? []).map((option) => option.value)).toEqual([
      "gemma4:26b-a4b-it-q4_K_M",
      "gemma4:12b",
      "qwen2.5:14b",
    ]);
  });

  it("does not save a blank model name", async () => {
    const user = userEvent.setup();
    const onSettingsChange = vi.fn();
    render(<ModelSettings settings={DEFAULT_MODEL_SETTINGS} onSettingsChange={onSettingsChange} />);

    const modelInput = await screen.findByLabelText("모델명");
    await waitFor(() => expect(modelInput).toHaveValue(DEFAULT_MODEL_SETTINGS.defaultModel));
    await user.clear(modelInput);
    await user.type(modelInput, "   ");

    expect(screen.getByText("모델명을 입력해주세요.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "저장" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "저장" }));

    expect(onSettingsChange).not.toHaveBeenCalled();
    expect(window.localStorage.getItem(MODEL_SETTINGS_STORAGE_KEY)).toBeNull();
  });
});
