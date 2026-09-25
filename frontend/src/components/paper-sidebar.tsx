"use client";

import { FileText, Sparkles, Library } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { UploadDialog } from "@/components/upload-dialog";
import type { Paper } from "@/lib/api";
import { cn } from "@/lib/utils";

export function PaperSidebar({
  papers,
  selectedId,
  onSelect,
  onUploaded,
}: {
  papers: Paper[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onUploaded: () => void;
}) {
  return (
    <aside className="flex h-full w-80 shrink-0 flex-col gap-4 border-r bg-sidebar p-5">
      <div className="flex items-center gap-2">
        <div className="flex size-9 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
          <Sparkles className="size-5" />
        </div>
        <div>
          <p className="text-lg font-semibold leading-none">paperpilot</p>
          <p className="text-xs text-muted-foreground">your research, with receipts</p>
        </div>
      </div>

      <UploadDialog onUploaded={onUploaded} />

      <Separator />

      <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Library className="size-3.5" />
        YOUR LIBRARY
      </div>

      <ScrollArea className="flex-1 -mx-1 px-1">
        <div className="flex flex-col gap-1.5">
          <button
            onClick={() => onSelect(null)}
            className={cn(
              "flex items-center justify-between rounded-2xl px-3 py-2.5 text-left text-sm transition-colors",
              selectedId === null
                ? "bg-primary text-primary-foreground shadow-sm"
                : "hover:bg-muted"
            )}
          >
            <span className="font-medium">All papers</span>
            <Badge
              variant="secondary"
              className={cn(
                "rounded-full",
                selectedId === null && "bg-primary-foreground/20 text-primary-foreground"
              )}
            >
              {papers.length}
            </Badge>
          </button>

          {papers.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              No papers yet. Upload one to get started.
            </p>
          )}

          {papers.map((p) => (
            <button
              key={p.paper_id}
              onClick={() => onSelect(p.paper_id)}
              className={cn(
                "flex flex-col gap-1 rounded-2xl px-3 py-2.5 text-left transition-colors",
                selectedId === p.paper_id
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "hover:bg-muted"
              )}
            >
              <span className="flex items-center gap-1.5 text-sm font-medium">
                <FileText className="size-3.5 shrink-0" />
                <span className="truncate">{p.title}</span>
              </span>
              <span
                className={cn(
                  "text-xs",
                  selectedId === p.paper_id
                    ? "text-primary-foreground/80"
                    : "text-muted-foreground"
                )}
              >
                {p.page_count} page{p.page_count === 1 ? "" : "s"}
              </span>
            </button>
          ))}
        </div>
      </ScrollArea>
    </aside>
  );
}
