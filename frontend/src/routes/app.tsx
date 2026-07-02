import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Send, Loader2, RefreshCw, Plus, ArrowUpRight, ThumbsUp, ThumbsDown, CornerDownLeft } from "lucide-react";
import ReactMarkdown from "react-markdown";

const API_BASE = "http://localhost:8090";

export const Route = createFileRoute("/app")({
  head: () => ({
    meta: [
      { title: "Engram — the archive" },
      { name: "description", content: "Query your second brain." },
    ],
  }),
  component: AppPage,
});

type Msg = { role: "user" | "engram"; text: string; sources?: string[]; fb?: number };

type Stats = {
  claude_cards: number;
  notion_pages: number;
  gmail_issues: number;
  notes: number;
  total_docs: number;
};

const sourceLabel: Record<string, string> = {
  claude_code: "src: claude_code",
  notion: "src: notion",
  gmail: "src: gmail",
  note: "src: note",
};

const SOURCES: { sync: string; name: string; desc: string; stat: (s: Stats) => string }[] = [
  { sync: "claude", name: "Claude Code", desc: "distilled coding sessions", stat: (s) => `${s.claude_cards} cards` },
  { sync: "notion", name: "Notion", desc: "notes, kept verbatim", stat: (s) => `${s.notion_pages} pages` },
  { sync: "gmail", name: "Gmail", desc: "AI / tech newsletters", stat: (s) => `${s.gmail_issues} issues` },
];

const SUGGESTIONS = [
  "What did I learn about chunking for RAG?",
  "How do I keep a knowledge graph consistent?",
  "What did I decide about running Docker services?",
];

function AppPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [syncing, setSyncing] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<Record<string, string>>({});
  const [stats, setStats] = useState<Stats | null>(null);
  const [note, setNote] = useState("");
  const [noteState, setNoteState] = useState<"idle" | "saving" | "saved" | "failed">("idle");
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      setStats(await res.json());
    } catch {
      /* keep old stats */
    }
  };

  // Load persisted thread (session id + messages) on mount — survives refresh & server restart.
  useEffect(() => {
    let sid = localStorage.getItem("engram_session");
    if (!sid) {
      sid = crypto.randomUUID();
      localStorage.setItem("engram_session", sid);
    }
    setSessionId(sid);
    const saved = localStorage.getItem("engram_messages");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch {
        /* ignore */
      }
    }
    loadStats();
    // Handoff from The Stacks: a card was clicked -> ask its question here.
    const pending = localStorage.getItem("engram_pending_q");
    if (pending) {
      localStorage.removeItem("engram_pending_q");
      ask(pending, sid);
    }
  }, []);

  // Persist messages.
  useEffect(() => {
    if (sessionId) localStorage.setItem("engram_messages", JSON.stringify(messages));
  }, [messages, sessionId]);

  // Auto-scroll to the newest message.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const newChat = () => {
    const sid = crypto.randomUUID();
    localStorage.setItem("engram_session", sid);
    localStorage.setItem("engram_messages", "[]");
    setSessionId(sid);
    setMessages([]);
  };

  const ask = async (question: string, sidOverride?: string) => {
    const q = question.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, session_id: sidOverride ?? sessionId }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "engram", text: data.answer, sources: data.sources ?? [] }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "engram", text: "⚠️ Couldn't reach your archive on " + API_BASE + " — is the API running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const syncSource = async (source: string) => {
    setSyncing(source);
    setSyncResult((r) => ({ ...r, [source]: "" }));
    try {
      const res = await fetch(`${API_BASE}/sync/${source}`, { method: "POST" });
      if (res.status === 409) {
        setSyncResult((r) => ({ ...r, [source]: "busy — try again" }));
        return;
      }
      const data = await res.json();
      setSyncResult((r) => ({
        ...r,
        [source]: data.added > 0 ? `+${data.added} new` : "up to date",
      }));
      loadStats();
    } catch {
      setSyncResult((r) => ({ ...r, [source]: "failed" }));
    } finally {
      setSyncing(null);
    }
  };

  const capture = async () => {
    const text = note.trim();
    if (!text || noteState === "saving") return;
    setNoteState("saving");
    try {
      const res = await fetch(`${API_BASE}/capture`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error();
      setNote("");
      setNoteState("saved");
      loadStats();
      setTimeout(() => setNoteState("idle"), 2500);
    } catch {
      setNoteState("failed");
      setTimeout(() => setNoteState("idle"), 2500);
    }
  };

  const giveFeedback = async (idx: number, score: number) => {
    const answer = messages[idx];
    if (!answer || answer.fb) return;
    // the question is the nearest preceding user message
    const question = [...messages.slice(0, idx)].reverse().find((m) => m.role === "user")?.text ?? "";
    setMessages((m) => m.map((msg, i) => (i === idx ? { ...msg, fb: score } : msg)));
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, question, answer: answer.text, score }),
      });
    } catch {
      /* feedback is best-effort */
    }
  };

  return (
    <div className="h-screen w-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Top bar */}
      <header className="h-14 border-b border-border shrink-0">
        <div className="h-full px-6 flex items-center justify-between">
          <Link to="/" className="t-label !text-foreground flex items-center gap-2.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber pulse-dot" />
            Engram
          </Link>
          <div className="flex items-center gap-5">
            <span className="t-label hidden sm:block">
              {stats ? `${stats.total_docs} entries` : "archive online"}
            </span>
            <Link to="/wall" className="t-label hover:!text-foreground transition-colors">
              The stacks
            </Link>
            <button onClick={newChat} className="btn-line px-3 py-1.5 flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5" /> New entry
            </button>
          </div>
        </div>
      </header>

      {/* Two panels */}
      <div className="flex-1 flex min-h-0">
        {/* Left: the reading room */}
        <div className="flex-1 flex flex-col border-r border-border min-h-0">
          <div className="flex-1 overflow-y-auto px-6 md:px-10 py-8 space-y-8">
            {messages.length === 0 && !loading && (
              <div className="h-full flex flex-col justify-center max-w-xl mx-auto">
                <p className="t-label mb-5">The reading room</p>
                <p className="font-display text-3xl md:text-4xl leading-snug text-foreground">
                  What are you trying to <em className="text-amber">remember?</em>
                </p>
                <p className="mt-4 text-sm text-muted-foreground leading-relaxed">
                  Your code sessions, notes and reading are one connected graph. Ask, then
                  follow up — it keeps the thread.
                </p>

                <div className="mt-8 divide-y divide-border border-y border-border">
                  {SUGGESTIONS.map((s, i) => (
                    <button
                      key={s}
                      onClick={() => ask(s)}
                      className="w-full text-left py-3.5 flex items-baseline gap-4 group cursor-pointer"
                    >
                      <span className="font-mono text-xs text-amber shrink-0">{String(i + 1).padStart(2, "0")}</span>
                      <span className="text-[0.95rem] text-foreground/75 group-hover:text-foreground transition-colors">
                        {s}
                      </span>
                      <ArrowUpRight className="w-3.5 h-3.5 ml-auto shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="max-w-2xl mx-auto space-y-8">
              {messages.map((m, i) =>
                m.role === "user" ? (
                  <div key={i}>
                    <p className="t-label mb-2">You asked</p>
                    <p className="font-display text-2xl leading-snug text-foreground">{m.text}</p>
                  </div>
                ) : (
                  <div key={i} className="card-arc">
                    <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                      <span className="t-label">Retrieved from memory</span>
                      {m.sources && m.sources.length > 0 && (
                        <span className="t-label !text-amber">
                          {m.sources.length} source{m.sources.length > 1 ? "s" : ""}
                        </span>
                      )}
                    </div>
                    <div className="p-5">
                      <div className="md-answer">
                        <ReactMarkdown>{m.text}</ReactMarkdown>
                      </div>
                      <div className="mt-4 pt-4 border-t border-border flex flex-wrap items-center gap-2">
                        {m.sources?.map((s) => (
                          <span key={s} className={`stamp ${s === "claude_code" ? "!text-amber !border-amber/40" : ""}`}>
                            {sourceLabel[s] ?? `src: ${s}`}
                          </span>
                        ))}
                        <span className="ml-auto flex items-center gap-1">
                          {m.fb ? (
                            <span className="t-label !text-amber">{m.fb > 0 ? "marked useful" : "marked off"}</span>
                          ) : (
                            <>
                              <button
                                onClick={() => giveFeedback(i, 1)}
                                title="Useful — reinforce this memory"
                                className="p-1.5 rounded-[3px] text-muted-foreground hover:text-amber hover:bg-amber/10 transition-colors cursor-pointer"
                              >
                                <ThumbsUp className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => giveFeedback(i, -1)}
                                title="Off — weaken this memory"
                                className="p-1.5 rounded-[3px] text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors cursor-pointer"
                              >
                                <ThumbsDown className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                ),
              )}
              {loading && (
                <div className="card-arc px-5 py-4 flex items-center gap-3">
                  <Loader2 className="w-4 h-4 animate-spin text-amber" />
                  <span className="t-label">Walking the graph…</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="border-t border-border shrink-0"
          >
            <div className="max-w-2xl mx-auto px-6 md:px-0 py-4 flex items-center gap-3">
              <span className="font-mono text-amber text-sm shrink-0">›</span>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="query the archive…"
                className="flex-1 bg-transparent outline-none text-[0.95rem] placeholder:text-muted-foreground/60 placeholder:font-mono placeholder:text-sm"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="btn-amber w-9 h-9 rounded-[3px] flex items-center justify-center shrink-0"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </form>
        </div>

        {/* Right: the index */}
        <aside className="w-[320px] hidden md:flex flex-col min-h-0">
          <div className="px-6 py-4 border-b border-border shrink-0">
            <p className="t-label !text-foreground">The index</p>
            <p className="text-xs text-muted-foreground mt-1">Sync pulls only what's new.</p>
          </div>
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
            {/* quick capture */}
            <div className="card-arc p-4">
              <p className="t-label mb-2.5">Remember this</p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  capture();
                }}
              >
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      capture();
                    }
                  }}
                  placeholder="a decision, an insight, anything…"
                  rows={2}
                  className="w-full bg-transparent outline-none text-sm resize-none placeholder:text-muted-foreground/60 leading-relaxed"
                />
                <div className="mt-2 flex items-center justify-between">
                  <span className="t-label !normal-case !tracking-normal">
                    {noteState === "saving" && "committing to memory…"}
                    {noteState === "saved" && <span className="!text-amber">remembered ✓</span>}
                    {noteState === "failed" && "failed — is the API up?"}
                    {noteState === "idle" && stats != null && `${stats.notes} notes so far`}
                  </span>
                  <button
                    type="submit"
                    disabled={!note.trim() || noteState === "saving"}
                    className="btn-amber px-2.5 py-1.5 flex items-center gap-1.5"
                  >
                    {noteState === "saving" ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <CornerDownLeft className="w-3 h-3" />
                    )}
                    remember
                  </button>
                </div>
              </form>
            </div>

            {SOURCES.map((s, i) => (
              <div key={s.sync} className="card-folder p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-2.5">
                      <span className="font-mono text-xs text-amber">{String(i + 1).padStart(2, "0")}</span>
                      <span className="font-display text-lg text-foreground">{s.name}</span>
                    </div>
                    <p className="t-label !normal-case !tracking-wide mt-1.5 pl-[26px]">{s.desc}</p>
                  </div>
                  <button
                    onClick={() => syncSource(s.sync)}
                    disabled={syncing !== null}
                    className="btn-line px-2.5 py-1.5 flex items-center gap-1.5 shrink-0"
                  >
                    {syncing === s.sync ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <RefreshCw className="w-3 h-3" />
                    )}
                    sync
                  </button>
                </div>
                <div className="mt-3 pl-[26px] flex items-center justify-between">
                  <span className="t-label">{stats ? s.stat(stats) : "—"}</span>
                  {syncResult[s.sync] && <span className="t-label !text-amber">{syncResult[s.sync]}</span>}
                </div>
              </div>
            ))}
            <p className="t-label !normal-case !tracking-normal leading-relaxed px-1 pt-3">
              Sync is manual — nothing runs in the background. Existing memory is never
              re-processed; only new entries pass through the graph. Ratings reshape future recall.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
