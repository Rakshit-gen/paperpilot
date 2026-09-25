"use client";

import { useCallback, useEffect, useState } from "react";
import { PaperSidebar } from "@/components/paper-sidebar";
import { AskPanel } from "@/components/ask-panel";
import { SummaryPanel } from "@/components/summary-panel";
import { FlashcardsPanel } from "@/components/flashcards-panel";
import { AuthScreen } from "@/components/auth-screen";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { listPapers, type Paper } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { toast } from "sonner";

export default function Home() {
  const { user, ready } = useAuth();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    listPapers()
      .then((r) => setPapers(r.papers))
      .catch(() => toast.error("couldn't reach the paperpilot backend"));
  }, []);

  useEffect(() => {
    if (user) refresh();
  }, [user, refresh]);

  if (!ready) return null;
  if (!user) return <AuthScreen />;

  const selectedPaper = papers.find((p) => p.paper_id === selectedId) ?? null;
  const scopedTitle = selectedPaper ? `"${selectedPaper.title}"` : "your library";

  return (
    <div className="flex h-screen">
      <PaperSidebar
        papers={papers}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onUploaded={refresh}
      />

      <main className="flex-1 overflow-y-auto p-8">
        <Tabs defaultValue="ask" className="h-full">
          <TabsList className="mb-6 rounded-2xl">
            <TabsTrigger value="ask" className="rounded-xl">Ask</TabsTrigger>
            <TabsTrigger value="summary" disabled={!selectedPaper} className="rounded-xl">
              Summary
            </TabsTrigger>
            <TabsTrigger value="flashcards" disabled={!selectedPaper} className="rounded-xl">
              Flashcards
            </TabsTrigger>
          </TabsList>

          <TabsContent value="ask" className="h-[calc(100%-3.5rem)]">
            <AskPanel paperId={selectedId} paperTitle={scopedTitle} papers={papers} />
          </TabsContent>

          <TabsContent value="summary" className="h-[calc(100%-3.5rem)]">
            {selectedPaper && (
              <SummaryPanel paperId={selectedPaper.paper_id} paperTitle={scopedTitle} />
            )}
          </TabsContent>

          <TabsContent value="flashcards" className="h-[calc(100%-3.5rem)]">
            {selectedPaper && (
              <FlashcardsPanel paperId={selectedPaper.paper_id} paperTitle={scopedTitle} />
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
