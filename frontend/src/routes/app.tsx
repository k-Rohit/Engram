import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Brain, Upload, HardDrive, Link as LinkIcon, Send, ChevronDown, Plus, Loader2, Check } from "lucide-react";

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
          <button className="flex items-center gap-2 text-sm text-[#9ca3af] hover:text-white px-3 py-1.5 rounded-lg border border-[#1f1f1f] hover:border-[#7c3aed]/50 transition">
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
        <div className="w-[60%] flex flex-col border-r border-[#1f1f1f] min-h-0">
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
            <div className="flex items-center gap-2 card-engram px-3 py-2">
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

        {/* Right: graph + ingest */}
        <div className="w-[40%] flex flex-col min-h-0">
          {/* Graph */}
          <div className="flex-1 border-b border-[#1f1f1f] p-4 min-h-0">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs uppercase tracking-widest text-[#6b7280]">Knowledge Graph</h3>
              <span className="text-[10px] text-[#6b7280]">247 nodes · 891 edges</span>
            </div>
            <div className="card-engram h-[calc(100%-2rem)] flex items-center justify-center bg-[#0a0a0a]">
              <GraphViz />
            </div>
          </div>

          {/* Ingest */}
          <div className="p-4 shrink-0">
            <h3 className="text-xs uppercase tracking-widest text-[#6b7280] mb-3">Ingest sources</h3>
            <div className="grid grid-cols-2 gap-2 mb-4">
              <IngestBtn icon={Brain} label="Sync Claude Code" />
              <IngestBtn icon={Upload} label="Upload ChatGPT Export" />
              <IngestBtn icon={HardDrive} label="Sync Google Drive" />
              <IngestBtn icon={LinkIcon} label="Add Article / URL" />
            </div>
            <ClaudeSessions />
          </div>
        </div>
      </div>
    </div>
  );
}

function IngestBtn({ icon: Icon, label }: { icon: any; label: string }) {
  return (
    <button className="btn-violet-outline rounded-lg px-3 py-2.5 text-xs flex items-center gap-2 justify-start">
      <Icon className="w-4 h-4 text-[#7c3aed] shrink-0" />
      <span className="truncate">{label}</span>
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

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-[10px] uppercase tracking-widest text-[#6b7280]">Claude Code sessions</h4>
        <button onClick={load} className="text-[10px] text-[#6b7280] hover:text-white">refresh</button>
      </div>

      {error && <div className="text-[11px] text-red-400 mb-2">{error}</div>}
      {!projects && !error && <div className="text-[11px] text-[#6b7280]">Loading…</div>}

      <div className="space-y-1.5 max-h-40 overflow-y-auto">
        {projects?.map((p) => (
          <div key={p.id} className="flex items-center justify-between text-xs px-3 py-2 rounded-lg hover:bg-[#111] transition">
            <div className="flex items-center gap-2 min-w-0">
              <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium border shrink-0 ${sourceColors.claude_code}`}>
                claude_code
              </span>
              <span className="text-white/80 truncate">{p.name}</span>
              <span className="text-[#6b7280] shrink-0">{p.sessions} · {p.lines} lines</span>
            </div>
            {p.ingested ? (
              <span className="flex items-center gap-1 text-[10px] text-emerald-400 shrink-0 ml-2">
                <Check className="w-3 h-3" /> ingested
              </span>
            ) : (
              <button
                onClick={() => ingest(p)}
                disabled={busy !== null}
                className="btn-violet px-2 py-1 rounded-md text-[10px] shrink-0 ml-2 disabled:opacity-40 flex items-center gap-1"
              >
                {busy === p.id ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                {busy === p.id ? "ingesting…" : "Ingest"}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function GraphViz() {
  const nodes = [
    { x: 180, y: 50, r: 10, c: "#7c3aed", label: "Claude" },
    { x: 70, y: 110, r: 8, c: "#06b6d4", label: "RAG" },
    { x: 300, y: 100, r: 9, c: "#06b6d4", label: "Notion" },
    { x: 180, y: 170, r: 14, c: "#7c3aed", label: "You" },
    { x: 60, y: 230, r: 8, c: "#7c3aed", label: "Medium" },
    { x: 310, y: 220, r: 9, c: "#06b6d4", label: "Drive" },
    { x: 180, y: 290, r: 10, c: "#7c3aed", label: "Cognee" },
    { x: 100, y: 320, r: 7, c: "#06b6d4", label: "Embeds" },
  ];
  const edges: Array<[number, number, string]> = [
    [0, 3, "uses"], [1, 3, "vs"], [2, 3, "stores"], [3, 4, "reads"],
    [3, 5, "syncs"], [3, 6, "powers"], [6, 7, "via"], [0, 6, "indexed"],
  ];
  return (
    <svg viewBox="0 0 380 360" className="w-full h-full">
      {edges.map(([a, b, lbl], i) => {
        const mx = (nodes[a].x + nodes[b].x) / 2;
        const my = (nodes[a].y + nodes[b].y) / 2;
        return (
          <g key={i}>
            <line x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} stroke="#1f1f1f" strokeWidth="1" />
            <text x={mx} y={my} fill="#4b5563" fontSize="8" textAnchor="middle" fontFamily="Poppins">{lbl}</text>
          </g>
        );
      })}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r + 6} fill={n.c} opacity="0.2" />
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.c} />
          <text x={n.x} y={n.y + n.r + 12} textAnchor="middle" fill="#9ca3af" fontSize="9" fontFamily="Poppins" fontWeight="500">{n.label}</text>
        </g>
      ))}
    </svg>
  );
}
