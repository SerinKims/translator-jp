"use client";

import { BookOpenText, Clock3, Languages, Library, Settings } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export type AppSection = "translate" | "viewer" | "history" | "glossary" | "settings";

const navItems: Array<{ id: AppSection; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: "translate", label: "번역 작업", icon: Languages },
  { id: "viewer", label: "번역본 보기", icon: BookOpenText },
  { id: "history", label: "번역 이력", icon: Clock3 },
  { id: "glossary", label: "용어집", icon: Library },
  { id: "settings", label: "모델 설정", icon: Settings },
];

export function AppSidebar({
  activeSection,
  onSectionChange,
}: {
  activeSection: AppSection;
  onSectionChange: (section: AppSection) => void;
}) {
  return (
    <aside className="flex min-h-screen w-full flex-col bg-slate-950 px-4 py-6 text-white lg:w-64">
      <div className="flex items-center gap-3 px-2">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-400 font-extrabold">T</div>
        <div>
          <div className="text-base font-extrabold">번역기</div>
          <div className="text-xs text-slate-400">URL · 텍스트 · 용어집</div>
        </div>
      </div>

      <Separator className="my-6 bg-white/10" />

      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Button
              key={item.id}
              type="button"
              variant="ghost"
              className={cn(
                "justify-start text-slate-300 hover:bg-white/10 hover:text-white",
                activeSection === item.id && "bg-white/10 text-white",
              )}
              onClick={() => onSectionChange(item.id)}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-lg bg-white/10 p-4 text-sm leading-6 text-slate-300">
        <strong className="text-white">권장 흐름</strong>
        <br />
        URL 또는 텍스트 입력 → 첫 page 번역 → 결과 확인 → 필요 시 전체 번역
      </div>
    </aside>
  );
}
