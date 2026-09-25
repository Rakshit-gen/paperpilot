"use client";

import { useState } from "react";
import { Loader2, Layers, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { generateFlashcards, type Flashcard } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function FlashcardTile({ card }: { card: Flashcard }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <Card
      onClick={() => setFlipped((f) => !f)}
      className={cn(
        "flex min-h-36 cursor-pointer flex-col justify-center gap-2 rounded-3xl p-5 text-center shadow-sm transition-colors",
        flipped ? "bg-accent" : "bg-card"
      )}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {flipped ? "answer" : "question"}
      </p>
      <p className="text-sm">{flipped ? card.answer : card.question}</p>
      <p className="mt-1 flex items-center justify-center gap-1 text-[11px] text-muted-foreground">
        <RotateCw className="size-3" /> tap to flip
      </p>
    </Card>
  );
}

export function FlashcardsPanel({ paperId, paperTitle }: { paperId: string; paperTitle: string }) {
  const [busy, setBusy] = useState(false);
  const [cards, setCards] = useState<Flashcard[]>([]);

  async function generate() {
    setBusy(true);
    try {
      const result = await generateFlashcards(paperId, 6);
      setCards(result.flashcards);
      if (result.flashcards.length === 0) toast.info("couldn't parse any flashcards, try again");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "couldn't generate flashcards");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Flashcards for {paperTitle}</h2>
          <p className="text-sm text-muted-foreground">
            Study cards grounded in the paper&apos;s own text, not a generic template.
          </p>
        </div>
        <Button onClick={generate} disabled={busy} className="rounded-2xl gap-2">
          {busy && <Loader2 className="size-4 animate-spin" />}
          {cards.length > 0 ? "Regenerate" : "Generate flashcards"}
        </Button>
      </div>

      {cards.length === 0 && !busy && (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-3xl border bg-card/50 text-center text-muted-foreground">
          <Layers className="size-8" />
          <p className="text-sm">No flashcards yet, generate a deck above.</p>
        </div>
      )}

      {cards.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((c, i) => (
            <FlashcardTile key={i} card={c} />
          ))}
        </div>
      )}
    </div>
  );
}
