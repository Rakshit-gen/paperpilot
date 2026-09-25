const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "paperpilot_token";

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

export type Session = {
  id: string;
  paper_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
};

export type SessionWithMessages = Session & {
  messages: { question: string; answer: string; created_at: string }[];
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore, e.g. private browsing with storage blocked
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `request failed with status ${res.status}`);
  }
  return res.json();
}

export function signup(email: string, password: string) {
  return request<{ token: string; user: { id: string; email: string } }>("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string) {
  return request<{ token: string; user: { id: string; email: string } }>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
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

export function askQuestion(question: string, paperId: string | null, sessionId: string | null) {
  return request<{ answer: string }>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, paper_id: paperId, session_id: sessionId }),
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

export function paperFileUrl(paperId: string, page?: number) {
  const token = getToken();
  const params = new URLSearchParams();
  if (token) params.set("token", token);
  const query = params.toString();
  const base = `${API_URL}/papers/${paperId}/file${query ? `?${query}` : ""}`;
  return page ? `${base}#page=${page}` : base;
}

export function createSession(paperId: string | null) {
  return request<Session>("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paper_id: paperId }),
  });
}

export function listSessions() {
  return request<{ sessions: Session[] }>("/sessions");
}

export function getSession(sessionId: string) {
  return request<SessionWithMessages>(`/sessions/${sessionId}`);
}

export function renameSession(sessionId: string, title: string) {
  return request<Session>(`/sessions/${sessionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export function deleteSession(sessionId: string) {
  return request<{ deleted: boolean }>(`/sessions/${sessionId}`, { method: "DELETE" });
}
