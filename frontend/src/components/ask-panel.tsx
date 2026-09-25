"use client";

import { useState } from "react";
import { Send, Loader2, MessageCircleQuestion, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { askQuestion } from "@/lib/api";
import type { ChatTurn } from "@/lib/types";
import { toast } from "sonner";

export function AskPanel({ paperId, paperTitle }: { paperId: string | null; paperTitle: string }) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([]);

  async function submit() {
    const q = question.trim();
    if (!q || busy) return;
    setBusy(true);
    setQuestion("");
    try {
      const result = await askQuestion(q, paperId);
      setTurns((t) => [...t, { question: q, answer: result.answer }]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "couldn't get an answer");
      setQuestion(q);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <h2 className="font-heading text-xl font-semibold">Ask {paperTitle}</h2>
        <p className="text-sm text-muted-foreground">
          Every answer is grounded in the text and cites the paper and page it came from.
          If the library doesn&apos;t have enough to answer, paperpilot says so instead of guessing.
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-3xl border bg-card/50 p-5">
        {turns.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <MessageCircleQuestion className="size-8 animate-float" />
            <p className="text-sm">Ask something like &quot;what method does this paper use?&quot;</p>
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} className="animate-in fade-in slide-in-from-bottom-2 space-y-3 duration-300">
            <div className="flex items-start justify-end gap-2">
              <Card className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-primary-foreground shadow-sm">
                <p className="text-sm">{turn.question}</p>
              </Card>
              <Avatar className="size-7 shrink-0">
                <AvatarFallback className="bg-secondary text-xs">you</AvatarFallback>
              </Avatar>
            </div>
            <div className="flex items-start gap-2">
              <Avatar className="size-7 shrink-0 bg-accent">
                <AvatarFallback className="bg-accent text-accent-foreground">
                  <Sparkles className="size-3.5" />
                </AvatarFallback>
              </Avatar>
              <Card className="max-w-[80%] animate-pop-in whitespace-pre-wrap rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm shadow-sm">
                {turn.answer}
              </Card>
            </div>
          </div>
        ))}

        {busy && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Reading the paper...
          </div>
        )}
      </div>

      <div className="flex items-end gap-2 rounded-3xl border bg-card p-2 shadow-sm">
        <Textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask a question about your papers..."
          className="min-h-11 resize-none border-0 shadow-none focus-visible:ring-0"
          rows={1}
        />
        <Button
          onClick={submit}
          disabled={busy || !question.trim()}
          size="icon"
          className="size-11 shrink-0 rounded-2xl transition-transform hover:scale-105 active:scale-90"
        >
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  );
}
