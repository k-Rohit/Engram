import { createFileRoute, Link } from "@tanstack/react-router";
import { Brain, FileText, Mail, Network, MessageSquare, ArrowRight, Sparkles } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Engram — Your second brain. Finally." },
      { name: "description", content: "Engram distills your Claude Code sessions, Notion notes, and the newsletters you read into one living knowledge graph. Ask anything you've ever learned." },
      { property: "og:title", content: "Engram — Your second brain. Finally." },
      { property: "og:description", content: "A personal second brain powered by a Cognee knowledge graph." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden relative">
      {/* Background: subtle grid + glows */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(124,58,237,0.15),transparent_55%)]" />
        <div
          className="absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
            maskImage: "radial-gradient(circle at 50% 30%, black, transparent 75%)",
          }}
        />
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-2 font-semibold text-lg">
          <span className="w-2 h-2 rounded-full bg-[#7c3aed] shadow-[0_0_12px_#7c3aed]" />
          Engram
        </div>
        <div className="flex items-center gap-6 text-sm text-[#9ca3af]">
          <a href="#how" className="hover:text-white transition hidden sm:block">How it works</a>
          <a href="#why" className="hover:text-white transition hidden sm:block">Why Engram</a>
          <Link to="/app" className="btn-violet px-4 py-2 rounded-lg text-white text-sm">Open App</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 px-8 pt-16 pb-8 max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#7c3aed]/30 bg-[#7c3aed]/10 text-xs text-[#c4b5fd] mb-8">
          <Sparkles className="w-3.5 h-3.5" />
          Powered by a Cognee knowledge graph
        </div>
        <h1 className="text-5xl md:text-7xl font-semibold tracking-tight leading-[1.03]">
          Your second brain.
          <br />
          <span className="bg-gradient-to-r from-[#a78bfa] via-[#7c3aed] to-[#22d3ee] bg-clip-text text-transparent">
            Finally.
          </span>
        </h1>
        <p className="mt-7 text-lg text-[#9ca3af] max-w-2xl mx-auto leading-relaxed">
          Engram distills your Claude Code sessions, Notion notes, and the newsletters you read into
          one living knowledge graph — then answers anything you've ever learned, with sources.
        </p>
        <div className="mt-9 flex items-center justify-center gap-3">
          <Link to="/app" className="btn-violet px-6 py-3 rounded-lg flex items-center gap-2">
            Open your brain <ArrowRight className="w-4 h-4" />
          </Link>
          <a href="#how" className="btn-ghost px-6 py-3 rounded-lg">See how it works</a>
        </div>

        {/* connected sources strip */}
        <div className="mt-10 flex items-center justify-center gap-2 flex-wrap text-xs text-[#6b7280]">
          <span className="mr-1">Connected:</span>
          {[
            { icon: Brain, label: "Claude Code" },
            { icon: FileText, label: "Notion" },
            { icon: Mail, label: "Gmail" },
          ].map((s) => (
            <span key={s.label} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#1f1f1f] bg-[#0f0f0f] text-[#d1d5db]">
              <s.icon className="w-3.5 h-3.5 text-[#a78bfa]" />
              {s.label}
            </span>
          ))}
        </div>
      </section>

      {/* Hero graph visual */}
      <section className="relative z-10 px-8 pb-24 max-w-4xl mx-auto">
        <div className="card-engram relative overflow-hidden p-6 md:p-10 bg-[#0a0a0a]">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(124,58,237,0.12),transparent_60%)]" />
          <GraphViz />
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="relative z-10 px-8 py-24 max-w-6xl mx-auto">
        <div className="mb-16 text-center">
          <div className="text-xs uppercase tracking-widest text-[#22d3ee] mb-3">How it works</div>
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight">Three steps to total recall.</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { icon: Brain, title: "Ingest", body: "Your Claude Code sessions are cleaned and distilled into insight cards; your Notion + newsletters flow in whole.", num: "01" },
            { icon: Network, title: "Connect", body: "Cognee builds one knowledge graph — linking concepts across everything you read and write.", num: "02" },
            { icon: MessageSquare, title: "Recall", body: "Ask in plain language. Get an answer traced back to the exact sources it came from.", num: "03" },
          ].map((s) => (
            <div
              key={s.title}
              className="group relative card-engram p-6 hover:border-[#7c3aed]/40 transition-colors overflow-hidden"
            >
              <div className="pointer-events-none absolute -top-8 -right-4 text-[6rem] font-bold text-white/[0.03] select-none">
                {s.num}
              </div>
              <div className="relative">
                <div className="w-12 h-12 rounded-2xl bg-[#7c3aed]/10 border border-[#7c3aed]/20 flex items-center justify-center mb-5 group-hover:bg-[#7c3aed]/20 transition-colors">
                  <s.icon className="w-6 h-6 text-[#a78bfa]" />
                </div>
                <h3 className="text-xl font-semibold mb-2 tracking-tight">{s.title}</h3>
                <p className="text-[#9ca3af] leading-relaxed text-[15px]">{s.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Why Engram */}
      <section id="why" className="relative z-10 px-8 py-24 max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-14 items-center">
          <div>
            <div className="text-xs uppercase tracking-widest text-[#22d3ee] mb-3">Why Engram</div>
            <h2 className="text-4xl md:text-5xl font-semibold mb-6 tracking-tight">
              Not search.
              <br />
              Memory.
            </h2>
            <p className="text-[#9ca3af] leading-relaxed text-lg mb-4">
              Vector RAG retrieves chunks of text by similarity. It finds passages — not understanding.
            </p>
            <p className="text-[#9ca3af] leading-relaxed text-lg">
              Engram builds a graph of the concepts, projects, and ideas across everything you read and
              write. Ask a question and it traverses the connections — the way you actually remember.
            </p>
          </div>
          <div className="card-engram p-8 aspect-square flex items-center justify-center bg-[#0a0a0a] relative overflow-hidden">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.08),transparent_60%)]" />
            <GraphViz compact />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 px-8 py-24 max-w-3xl mx-auto text-center">
        <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-5">
          Stop re-learning what you already know.
        </h2>
        <p className="text-[#9ca3af] text-lg mb-9">
          Every answer you've ever gotten, every note you've written, every article you've read — one brain.
        </p>
        <Link to="/app" className="btn-violet px-7 py-3.5 rounded-lg inline-flex items-center gap-2">
          Open your brain <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="relative z-10 px-8 py-10 border-t border-[#1f1f1f]">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-[#6b7280]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#7c3aed]" />
            Built with Cognee
          </div>
          <div>© 2026 Engram</div>
        </div>
      </footer>
    </div>
  );
}

function GraphViz({ compact = false }: { compact?: boolean }) {
  const nodes = [
    { x: 300, y: 190, r: 22, c: "#7c3aed", label: "You", big: true },
    { x: 120, y: 80, r: 13, c: "#a78bfa", label: "Claude Code" },
    { x: 470, y: 90, r: 12, c: "#e5e7eb", label: "Notion" },
    { x: 510, y: 230, r: 12, c: "#fca5a5", label: "Gmail" },
    { x: 150, y: 300, r: 11, c: "#22d3ee", label: "RAG" },
    { x: 340, y: 330, r: 12, c: "#22d3ee", label: "Knowledge Graph" },
    { x: 90, y: 200, r: 10, c: "#a78bfa", label: "Chunking" },
    { x: 460, y: 340, r: 10, c: "#7c3aed", label: "Cognee" },
  ];
  const edges: [number, number][] = [
    [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [1, 6], [4, 6], [5, 7], [3, 2], [1, 4], [5, 7],
  ];
  return (
    <svg viewBox="0 0 600 400" className="w-full h-full relative">
      <defs>
        <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.3" />
        </linearGradient>
      </defs>
      {edges.map(([a, b], i) => (
        <line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} stroke="url(#edge)" strokeWidth="1.5" />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r + 10} fill={n.c} opacity="0.14">
            <animate attributeName="opacity" values="0.08;0.2;0.08" dur={`${3 + (i % 3)}s`} repeatCount="indefinite" />
          </circle>
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.c} opacity={n.big ? 1 : 0.9} />
          {n.big && <circle cx={n.x} cy={n.y} r={n.r} fill="none" stroke="#fff" strokeOpacity="0.25" strokeWidth="1.5" />}
          {!compact && (
            <text x={n.x} y={n.y + n.r + 16} textAnchor="middle" fill="#9ca3af" fontSize="11" fontWeight="500" fontFamily="Poppins">
              {n.label}
            </text>
          )}
        </g>
      ))}
    </svg>
  );
}
