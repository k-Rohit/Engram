import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Brain, FileText, Mail, Send, Loader2, Check, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";

const API_BASE = "http://localhost:8090";

export const Route = createFileRoute("/app")({
  head: () => ({
    meta: [
      { title: "Engram — App" },
      { name: "description", content: "Query your second brain." },
    ],
  }),
  component: AppPage,
});

type Msg = { role: "user" | "engram"; text: string; sources?: string[] };

const sourceMeta: Record<string, { label: string; cls: string }> = {
  claude_code: { label: "Claude Code", cls: "bg-[#7c3aed]/15 text-[#a78bfa] border-[#7c3aed]/30" },
  notion: { label: "Notion", cls: "bg-white/5 text-[#e5e7eb] border-white/15" },
  gmail: { label: "Gmail", cls: "bg-[#ef4444]/12 text-[#fca5a5] border-[#ef4444]/25" },
};

const CONNECTED = [
  { key: "claude_code", icon: Brain, label: "Claude Code", desc: "Distilled coding sessions" },
  { key: "notion", icon: FileText, label: "Notion", desc: "Your written notes" },
  { key: "gmail", icon: Mail, label: "Gmail", desc: "AI / tech newsletters" },
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
  // One session id per chat → Cognee session memory, so follow-ups keep context.
  const [sessionId] = useState(() => crypto.randomUUID());

  const ask = async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "engram", text: data.answer, sources: data.sources ?? [] }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "engram", text: "⚠️ Couldn't reach your brain on " + API_BASE + " — is the API running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 h-14 border-b border-[#1f1f1f] shrink-0">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="w-2 h-2 rounded-full bg-[#7c3aed] shadow-[0_0_12px_#7c3aed]" />
          Engram
        </Link>
        <div className="flex items-center gap-2 text-xs text-[#6b7280]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          brain online
        </div>
      </header>

      {/* Two panels */}
      <div className="flex-1 flex min-h-0">
        {/* Left: chat */}
        <div className="flex-1 flex flex-col border-r border-[#1f1f1f] min-h-0">
          <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
            {messages.length === 0 && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center px-8">
                <div className="w-14 h-14 rounded-2xl bg-[#7c3aed]/10 border border-[#7c3aed]/20 flex items-center justify-center mb-5">
                  <Brain className="w-7 h-7 text-[#a78bfa]" />
                </div>
                <p className="text-lg text-white font-medium">Ask your second brain</p>
                <p className="text-sm text-[#6b7280] mt-1.5 max-w-md">
                  Everything from your code, notes, and reading — connected in one graph.
                </p>
                <div className="mt-6 flex flex-col gap-2 w-full max-w-md">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => ask(s)}
                      className="text-left text-sm text-[#9ca3af] hover:text-white border border-[#1f1f1f] hover:border-[#7c3aed]/40 rounded-xl px-4 py-2.5 transition cursor-pointer flex items-center gap-2"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-[#7c3aed] shrink-0" />
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "user" ? (
                  <div className="max-w-[75%] px-4 py-3 rounded-2xl bg-[#7c3aed] text-white text-sm leading-relaxed">
                    {m.text}
                  </div>
                ) : (
                  <div className="max-w-[85%] card-engram p-4 border-l-2 border-l-[#06b6d4]">
                    <div className="md-answer">
                      <ReactMarkdown>{m.text}</ReactMarkdown>
                    </div>
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        <span className="text-[10px] text-[#6b7280] mr-1 self-center">sources:</span>
                        {m.sources.map((s) => (
                          <span
                            key={s}
                            className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${sourceMeta[s]?.cls ?? "bg-white/5 text-[#9ca3af] border-white/10"}`}
                          >
                            {sourceMeta[s]?.label ?? s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="card-engram p-4 border-l-2 border-l-[#06b6d4] flex items-center gap-2 text-sm text-[#9ca3af]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#a78bfa]" />
                  Searching your memory…
                </div>
              </div>
            )}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="p-4 border-t border-[#1f1f1f] shrink-0"
          >
            <div className="flex items-center gap-2 card-engram px-3 py-2 focus-within:border-[#7c3aed]/50 transition-colors">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything you've learned..."
                className="flex-1 bg-transparent outline-none text-sm placeholder:text-[#6b7280] px-2"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="btn-violet w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </form>
        </div>

        {/* Right: connected sources */}
        <aside className="w-[320px] flex flex-col min-h-0 bg-[#0b0b0b]">
          <div className="px-6 py-4 border-b border-[#1f1f1f] shrink-0">
            <h2 className="text-sm font-semibold text-white">Connected Sources</h2>
            <p className="text-xs text-[#6b7280] mt-0.5">All feeding one unified graph.</p>
          </div>
          <div className="flex-1 overflow-y-auto px-4 py-5 space-y-3">
            {CONNECTED.map((s) => (
              <div
                key={s.key}
                className="flex items-center gap-3 px-3.5 py-3 rounded-xl border border-[#1f1f1f] bg-[#101010]"
              >
                <span className="w-10 h-10 rounded-xl bg-[#7c3aed]/10 border border-[#7c3aed]/20 flex items-center justify-center shrink-0">
                  <s.icon className="w-5 h-5 text-[#a78bfa]" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-white">{s.label}</div>
                  <div className="text-[11px] text-[#6b7280] truncate">{s.desc}</div>
                </div>
                <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-400 shrink-0">
                  <Check className="w-3.5 h-3.5" /> live
                </span>
              </div>
            ))}
            <p className="text-[11px] text-[#4b5563] px-1 pt-2 leading-relaxed">
              Your code, notes, and reading are distilled into one Cognee knowledge graph — so answers
              connect across all of them.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
