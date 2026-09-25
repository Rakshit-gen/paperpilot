"use client";

import { useState } from "react";
import { Loader2, ScrollText, Target, FlaskConical, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { summarizePaper } from "@/lib/api";
import { toast } from "sonner";

function parseSummary(raw: string) {
  const sections: { label: string; icon: typeof Target; text: string }[] = [];
  const pattern = /(Problem|Method|Result):\s*/g;
  const matches = [...raw.matchAll(pattern)];
  const icons = { Problem: Target, Method: FlaskConical, Result: Trophy };

  if (matches.length === 0) return [{ label: "Summary", icon: ScrollText, text: raw }];

  matches.forEach((m, i) => {
    const start = m.index! + m[0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index! : raw.length;
    sections.push({
      label: m[1],
      icon: icons[m[1] as keyof typeof icons],
      text: raw.slice(start, end).trim(),
    });
  });
  return sections;
}

export function SummaryPanel({ paperId, paperTitle }: { paperId: string; paperTitle: string }) {
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);

  async function generate() {
    setBusy(true);
    try {
      const result = await summarizePaper(paperId);
      setSummary(result.summary);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "couldn't summarize this paper");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Summary of {paperTitle}</h2>
          <p className="text-sm text-muted-foreground">
            Problem, method, and result, pulled only from this paper&apos;s own text.
          </p>
        </div>
        <Button onClick={generate} disabled={busy} className="rounded-2xl gap-2">
          {busy && <Loader2 className="size-4 animate-spin" />}
          {summary ? "Regenerate" : "Generate summary"}
        </Button>
      </div>

      {!summary && !busy && (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-3xl border bg-card/50 text-center text-muted-foreground">
          <ScrollText className="size-8" />
          <p className="text-sm">No summary yet, generate one above.</p>
        </div>
      )}

      {summary && (
        <div className="grid gap-4 sm:grid-cols-3">
          {parseSummary(summary).map((s) => (
            <Card key={s.label} className="rounded-3xl p-5 shadow-sm">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-primary">
                <s.icon className="size-4" />
                {s.label}
              </div>
              <p className="text-sm text-muted-foreground">{s.text}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
