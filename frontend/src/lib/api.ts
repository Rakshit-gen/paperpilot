const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Paper = {
  paper_id: string;
  title: string;
  filename: string;
  page_count: number;
  uploaded_at: string;
};

export type Citation = {
  text: string;
  title: string;
  page: number;
};

export type Flashcard = {
  question: string;
  answer: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `request failed with status ${res.status}`);
  }
  return res.json();
}

export function listPapers() {
  return request<{ papers: Paper[] }>("/papers");
}

export async function uploadPaper(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ paper_id: string; title: string; chunks: number; pages: number }>(
    "/papers/upload",
    { method: "POST", body: form }
  );
}

export function askQuestion(question: string, paperId: string | null) {
  return request<{ answer: string }>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, paper_id: paperId }),
  });
}

export function summarizePaper(paperId: string) {
  return request<{ paper_id: string; title: string; summary: string }>(
    `/papers/${paperId}/summarize`,
    { method: "POST" }
  );
}

export function generateFlashcards(paperId: string, count = 5) {
  return request<{ paper_id: string; title: string; flashcards: Flashcard[] }>(
    `/papers/${paperId}/flashcards?count=${count}`,
    { method: "POST" }
  );
}
