"use client";

import { useState } from "react";
import { Loader2, Layers, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { generateFlashcards, type Flashcard } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function FlashcardTile({ card, delay }: { card: Flashcard; delay: number }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <div
      onClick={() => setFlipped((f) => !f)}
      style={{ perspective: "1200px", animationDelay: `${delay}ms` }}
      className="h-40 w-full animate-in fade-in slide-in-from-bottom-2 cursor-pointer duration-300"
    >
      <div
        className={cn(
          "flip-card-inner relative h-full w-full",
          flipped && "[transform:rotateY(180deg)]"
        )}
      >
        <Card className="flip-card-face absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-3xl p-5 text-center shadow-sm hover:shadow-md">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            question
          </p>
          <p className="text-sm">{card.question}</p>
          <p className="mt-1 flex items-center justify-center gap-1 text-[11px] text-muted-foreground">
            <RotateCw className="size-3" /> tap to flip
          </p>
        </Card>
        <Card className="flip-card-face flip-card-back absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-3xl bg-accent p-5 text-center text-accent-foreground shadow-sm hover:shadow-md">
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">answer</p>
          <p className="text-sm">{card.answer}</p>
          <p className="mt-1 flex items-center justify-center gap-1 text-[11px] opacity-70">
            <RotateCw className="size-3" /> tap to flip back
          </p>
        </Card>
      </div>
    </div>
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
          <h2 className="font-heading text-xl font-semibold">Flashcards for {paperTitle}</h2>
          <p className="text-sm text-muted-foreground">
            Study cards grounded in the paper&apos;s own text, not a generic template.
          </p>
        </div>
        <Button
          onClick={generate}
          disabled={busy}
          className="rounded-2xl gap-2 transition-transform hover:scale-[1.03] active:scale-95"
        >
          {busy && <Loader2 className="size-4 animate-spin" />}
          {cards.length > 0 ? "Regenerate" : "Generate flashcards"}
        </Button>
      </div>

      {cards.length === 0 && !busy && (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-3xl border bg-card/50 text-center text-muted-foreground">
          <Layers className="size-8 animate-float" />
          <p className="text-sm">No flashcards yet, generate a deck above.</p>
        </div>
      )}

      {cards.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((c, i) => (
            <FlashcardTile key={i} card={c} delay={i * 60} />
          ))}
        </div>
      )}
    </div>
  );
}
