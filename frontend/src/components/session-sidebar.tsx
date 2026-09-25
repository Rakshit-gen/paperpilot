"use client";

import { useState } from "react";
import { MessageSquarePlus, Pencil, Trash2, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Paper, Session } from "@/lib/api";
import { cn } from "@/lib/utils";

export function SessionSidebar({
  sessions,
  activeSessionId,
  papers,
  onSelect,
  onNew,
  onRename,
  onDelete,
}: {
  sessions: Session[];
  activeSessionId: string | null;
  papers: Paper[];
  onSelect: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");

  function startEdit(session: Session) {
    setEditingId(session.id);
    setDraftTitle(session.title);
  }

  function commitEdit() {
    if (editingId && draftTitle.trim()) onRename(editingId, draftTitle.trim());
    setEditingId(null);
  }

  return (
    <div className="flex h-full w-64 shrink-0 flex-col gap-3 border-r pr-4">
      <Button
        onClick={onNew}
        variant="secondary"
        className="w-full justify-start gap-2 rounded-2xl"
      >
        <MessageSquarePlus className="size-4" />
        New chat
      </Button>

      <ScrollArea className="flex-1 -mx-1 px-1">
        <div className="flex flex-col gap-1">
          {sessions.length === 0 && (
            <p className="px-2 py-6 text-center text-xs text-muted-foreground">
              Your conversations will show up here.
            </p>
          )}

          {sessions.map((s) => {
            const scope = s.paper_id ? papers.find((p) => p.paper_id === s.paper_id)?.title : null;
            const editing = editingId === s.id;
            return (
              <div
                key={s.id}
                className={cn(
                  "group flex items-center gap-1 rounded-xl px-2 py-2 text-left text-sm transition-colors",
                  activeSessionId === s.id ? "bg-primary/15" : "hover:bg-muted"
                )}
              >
                {editing ? (
                  <div className="flex flex-1 items-center gap-1">
                    <Input
                      autoFocus
                      value={draftTitle}
                      onChange={(e) => setDraftTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") commitEdit();
                        if (e.key === "Escape") setEditingId(null);
                      }}
                      className="h-7 text-xs"
                    />
                    <button onClick={commitEdit} className="shrink-0 text-muted-foreground hover:text-foreground">
                      <Check className="size-3.5" />
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="shrink-0 text-muted-foreground hover:text-foreground"
                    >
                      <X className="size-3.5" />
                    </button>
                  </div>
                ) : (
                  <>
                    <button onClick={() => onSelect(s.id)} className="min-w-0 flex-1 text-left">
                      <span className="block truncate font-medium">{s.title}</span>
                      {scope && (
                        <span className="block truncate text-xs text-muted-foreground">{scope}</span>
                      )}
                    </button>
                    <button
                      onClick={() => startEdit(s)}
                      className="hidden shrink-0 text-muted-foreground hover:text-foreground group-hover:block"
                    >
                      <Pencil className="size-3.5" />
                    </button>
                    <button
                      onClick={() => onDelete(s.id)}
                      className="hidden shrink-0 text-muted-foreground hover:text-destructive group-hover:block"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
