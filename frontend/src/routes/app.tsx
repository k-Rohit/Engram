import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Brain,
  Upload,
  HardDrive,
  Link as LinkIcon,
  Send,
  ChevronDown,
  Plus,
  Loader2,
  Check,
  RefreshCw,
  FileText,
} from "lucide-react";

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

const sourceColors: Record<string, string> = {
  claude_code: "bg-[#7c3aed]/15 text-[#a78bfa] border-[#7c3aed]/30",
  chatgpt: "bg-[#06b6d4]/15 text-[#67e8f9] border-[#06b6d4]/30",
  medium: "bg-white/5 text-[#9ca3af] border-white/10",
  google_drive: "bg-[#06b6d4]/10 text-[#22d3ee] border-[#06b6d4]/20",
};

type ClaudeProject = {
  id: string;
  name: string;
  dataset: string;
  sessions: number;
  lines: number;
  ingested: boolean;
};

function AppPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: "user", text: "What did I conclude about graph memory vs vector RAG last month?" },
    {
      role: "engram",
      text: "You found that vector RAG retrieved semantically similar chunks but missed multi-hop reasoning. Your notes converged on graph memory (via Cognee) for any query that needs to traverse concept relationships — e.g. \"how does my project X connect to idea Y I read in March.\"",
      sources: ["claude_code", "medium", "google_drive"],
    },
  ]);
  const [input, setInput] = useState("");

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((m) => [
      ...m,
      { role: "user", text: input },
      {
        role: "engram",
        text: "Based on your ingested sources, here's what I remember about that. Cross-referencing your Claude sessions and Medium reads from the last 30 days.",
        sources: ["claude_code", "chatgpt", "medium"],
      },
    ]);
    setInput("");
  };

  return (
    <div className="h-screen w-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 h-14 border-b border-[#1f1f1f] shrink-0">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="w-2 h-2 rounded-full bg-[#7c3aed] shadow-[0_0_12px_#7c3aed]" />
          Engram
        </Link>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 text-sm text-[#9ca3af] hover:text-white px-3 py-1.5 rounded-lg border border-[#1f1f1f] hover:border-[#7c3aed]/50 transition cursor-pointer">
            personal-brain
            <ChevronDown className="w-4 h-4" />
          </button>
          <button className="btn-violet px-3 py-1.5 rounded-lg text-sm flex items-center gap-1.5">
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </div>
      </header>

      {/* Two panels */}
      <div className="flex-1 flex min-h-0">
        {/* Left: chat */}
        <div className="w-[58%] flex flex-col border-r border-[#1f1f1f] min-h-0">
          <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "user" ? (
                  <div className="max-w-[75%] px-4 py-3 rounded-2xl bg-[#7c3aed] text-white text-sm leading-relaxed">
                    {m.text}
                  </div>
                ) : (
                  <div className="max-w-[80%] card-engram p-4 border-l-2 border-l-[#06b6d4]">
                    <p className="text-sm leading-relaxed text-white/90">{m.text}</p>
                    {m.sources && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {m.sources.map((s) => (
                          <span key={s} className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${sourceColors[s]}`}>
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
          <form onSubmit={send} className="p-4 border-t border-[#1f1f1f] shrink-0">
            <div className="flex items-center gap-2 card-engram px-3 py-2 focus-within:border-[#7c3aed]/50 transition-colors">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything you've learned..."
                className="flex-1 bg-transparent outline-none text-sm placeholder:text-[#6b7280] px-2"
              />
              <button type="submit" className="btn-violet w-9 h-9 rounded-lg flex items-center justify-center shrink-0">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Right: memory sources */}
        <aside className="w-[42%] flex flex-col min-h-0 bg-[#0b0b0b]">
          <div className="px-6 py-4 border-b border-[#1f1f1f] shrink-0">
            <h2 className="text-sm font-semibold text-white">Memory Sources</h2>
            <p className="text-xs text-[#6b7280] mt-0.5">Feed your second brain — ingest from any source.</p>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-7">
            {/* Connect a source */}
            <section>
              <h3 className="text-[11px] uppercase tracking-widest text-[#6b7280] mb-3">Connect a source</h3>
              <div className="grid grid-cols-2 gap-3">
                <SourceCard icon={Brain} label="Claude Code" hint="Sync transcripts" />
                <SourceCard icon={Upload} label="ChatGPT" hint="Upload export" />
                <SourceCard icon={HardDrive} label="Google Drive" hint="Sync docs" />
                <SourceCard icon={LinkIcon} label="Article / URL" hint="Paste a link" />
              </div>
            </section>

            {/* Claude Code sessions */}
            <ClaudeSessions />
          </div>
        </aside>
      </div>
    </div>
  );
}

function SourceCard({ icon: Icon, label, hint }: { icon: any; label: string; hint: string }) {
  return (
    <button className="source-card group p-4 flex flex-col items-start gap-3 text-left">
      <span className="w-10 h-10 rounded-xl bg-[#7c3aed]/10 border border-[#7c3aed]/20 flex items-center justify-center group-hover:bg-[#7c3aed]/20 transition-colors">
        <Icon className="w-5 h-5 text-[#a78bfa]" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-medium text-white truncate">{label}</span>
        <span className="block text-[11px] text-[#6b7280] truncate">{hint}</span>
      </span>
    </button>
  );
}

function ClaudeSessions() {
  const [projects, setProjects] = useState<ClaudeProject[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await fetch(`${API_BASE}/claude/projects`);
      setProjects(await res.json());
      setError(null);
    } catch {
      setError(`Can't reach the Engram backend on ${API_BASE}`);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const ingest = async (p: ClaudeProject) => {
    setBusy(p.id);
    try {
      await fetch(`${API_BASE}/ingest/claude-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_project: p.id }),
      });
      await load();
    } catch {
      setError(`Ingest failed for ${p.name}`);
    } finally {
      setBusy(null);
    }
  };

  const ingestedCount = projects?.filter((p) => p.ingested).length ?? 0;

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[11px] uppercase tracking-widest text-[#6b7280]">
          Claude Code sessions
          {projects && (
            <span className="ml-2 text-[#a78bfa] normal-case tracking-normal">
              {ingestedCount}/{projects.length} ingested
            </span>
          )}
        </h3>
        <button
          onClick={load}
          className="flex items-center gap-1 text-[11px] text-[#6b7280] hover:text-white transition cursor-pointer"
        >
          <RefreshCw className="w-3 h-3" /> refresh
        </button>
      </div>

      {error && (
        <div className="text-[12px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 mb-3">
          {error}
        </div>
      )}
      {!projects && !error && (
        <div className="flex items-center gap-2 text-[12px] text-[#6b7280] px-1 py-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading projects…
        </div>
      )}

      <div className="space-y-2">
        {projects?.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between gap-3 px-3.5 py-3 rounded-xl border border-[#1f1f1f] bg-[#101010] hover:border-[#7c3aed]/30 hover:bg-[#141414] transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="w-9 h-9 rounded-lg bg-[#7c3aed]/10 border border-[#7c3aed]/20 flex items-center justify-center shrink-0">
                <FileText className="w-4 h-4 text-[#a78bfa]" />
              </span>
              <div className="min-w-0">
                <div className="text-sm text-white/90 font-medium truncate">{p.name}</div>
                <div className="text-[11px] text-[#6b7280]">
                  {p.sessions} session{p.sessions !== 1 ? "s" : ""} · {p.lines.toLocaleString()} lines
                </div>
              </div>
            </div>

            {p.ingested ? (
              <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-2.5 py-1 shrink-0">
                <Check className="w-3.5 h-3.5" /> Ingested
              </span>
            ) : (
              <button
                onClick={() => ingest(p)}
                disabled={busy !== null}
                className="btn-violet px-3 py-1.5 rounded-lg text-xs shrink-0 flex items-center gap-1.5"
              >
                {busy === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                {busy === p.id ? "Ingesting…" : "Ingest"}
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
