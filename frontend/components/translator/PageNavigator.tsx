"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function PageNavigator({
  currentPageIndex,
  onPageChange,
  pageCount,
}: {
  currentPageIndex: number;
  onPageChange: (index: number) => void;
  pageCount: number;
}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap gap-2">
        {pageCount === 0 ? (
          <span className="text-sm text-muted-foreground">페이지 없음</span>
        ) : (
          Array.from({ length: pageCount }, (_, index) => (
            <Button
              key={index}
              type="button"
              variant={index === currentPageIndex ? "default" : "outline"}
              size="sm"
              className={cn("min-w-20", index === currentPageIndex && "shadow-sm")}
              onClick={() => onPageChange(index)}
            >
              page {index + 1}
            </Button>
          ))
        )}
      </div>

      <div className="flex gap-2">
        <Button type="button" variant="outline" size="sm" disabled={currentPageIndex <= 0} onClick={() => onPageChange(currentPageIndex - 1)}>
          <ChevronLeft className="h-4 w-4" />
          이전 페이지
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pageCount === 0 || currentPageIndex >= pageCount - 1}
          onClick={() => onPageChange(currentPageIndex + 1)}
        >
          다음 페이지
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
