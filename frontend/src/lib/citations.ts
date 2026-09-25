import { paperFileUrl, type Paper } from "@/lib/api";

const CITATION_BRACKET = /\[([^[\]]+)\]/g;
const CITATION_ENTRY = /^\s*(.+?),\s*page\s*(\d+)\s*$/i;

/**
 * Turns the model's inline `[title, page N]` citations (it can also chain
 * several as `[title, page N; title, page M]`) into markdown links pointing
 * at the source PDF, so clicking one opens the actual document at that page.
 * Anything that doesn't match a known paper is left as plain text.
 */
export function linkifyCitations(text: string, papers: Paper[]): string {
  const byTitle = new Map(papers.map((p) => [p.title.trim().toLowerCase(), p.paper_id]));

  return text.replace(CITATION_BRACKET, (whole, inner: string) => {
    const parts = inner.split(";").map((part) => part.trim());
    const linked = parts.map((part) => {
      const match = part.match(CITATION_ENTRY);
      if (!match) return null;
      const [, title, page] = match;
      const paperId = byTitle.get(title.trim().toLowerCase());
      if (!paperId) return null;
      return `[${title}, page ${page}](${paperFileUrl(paperId, Number(page))})`;
    });
    if (linked.some((l) => l === null)) return whole;
    return linked.join("; ");
  });
}
