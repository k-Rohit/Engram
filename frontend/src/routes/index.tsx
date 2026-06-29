import { createFileRoute, Link } from "@tanstack/react-router";
import { Brain, Network, MessageSquare } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Engram — Your second brain. Finally." },
      { name: "description", content: "Engram ingests your Claude, ChatGPT, Medium articles, and notes into a living knowledge graph. Ask anything you've ever learned." },
      { property: "og:title", content: "Engram — Your second brain. Finally." },
      { property: "og:description", content: "A personal second brain powered by a living knowledge graph." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <Link to="/" className="flex items-center gap-2 font-semibold text-lg">
          <span className="w-2 h-2 rounded-full bg-[#7c3aed] shadow-[0_0_12px_#7c3aed]" />
          Engram
        </Link>
        <div className="flex items-center gap-6 text-sm text-[#6b7280]">
          <a href="#how" className="hover:text-white transition">How it works</a>
          <a href="#why" className="hover:text-white transition">Why Engram</a>
          <Link to="/app" className="btn-violet px-4 py-2 rounded-lg text-white">Open App</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative px-8 pt-20 pb-32 max-w-7xl mx-auto">
        {/* gradient blobs */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="blob-animate absolute top-10 left-1/4 w-[500px] h-[500px] rounded-full bg-[#7c3aed] opacity-[0.12] blur-[120px]" />
          <div className="blob-animate absolute top-40 right-1/4 w-[400px] h-[400px] rounded-full bg-[#06b6d4] opacity-[0.10] blur-[120px]" style={{ animationDelay: "-6s" }} />
        </div>

        <div className="relative text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1f1f1f] bg-[#111] text-xs text-[#6b7280] mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-[#06b6d4]" />
            Powered by Cognee knowledge graphs
          </div>
          <h1 className="text-6xl md:text-7xl font-semibold tracking-tight leading-[1.05]">
            Your second brain.<br />Finally.
          </h1>
          <p className="mt-8 text-lg text-[#6b7280] max-w-2xl mx-auto leading-relaxed">
            Engram ingests your Claude, ChatGPT, Medium articles, and notes into a living knowledge graph. Ask anything you've ever learned.
          </p>
          <div className="mt-10 flex items-center justify-center gap-3">
            <Link to="/app" className="btn-violet px-6 py-3 rounded-lg">Get Started</Link>
            <a href="#how" className="btn-ghost px-6 py-3 rounded-lg">See how it works</a>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="relative px-8 py-32 max-w-6xl mx-auto overflow-hidden">
        {/* subtle radial glows */}
        <div className="pointer-events-none absolute -top-1/2 -left-1/4 w-full h-full bg-[#7c3aed]/[0.08] blur-[120px] rounded-full" />
        <div className="pointer-events-none absolute -bottom-1/2 -right-1/4 w-full h-full bg-[#06b6d4]/[0.05] blur-[120px] rounded-full" />

        <div className="relative mb-20">
          <div className="text-xs uppercase tracking-widest text-[#06b6d4] mb-3">How it works</div>
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight">Three steps to total recall.</h2>
        </div>

        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-16 lg:gap-20">
          {[
            { icon: Brain, title: "Ingest", body: "Connect Claude Code, ChatGPT exports, Medium articles, and Google Drive — effortlessly.", num: "01", color: "#7c3aed" },
            { icon: Network, title: "Remember", body: "Cognee builds a living knowledge graph of everything you've learned, in real time.", num: "02", color: "#22d3ee" },
            { icon: MessageSquare, title: "Recall", body: "Ask anything. Get cited answers traced back to your own memory.", num: "03", color: "#7c3aed" },
          ].map((s, i) => (
            <div key={s.title} className="group relative">
              <span
                className="absolute -top-16 -left-4 text-[8rem] leading-none font-bold select-none pointer-events-none text-white/[0.03] transition-colors duration-500"
                style={{ ['--hover-c' as any]: s.color }}
              >
                {s.num}
              </span>
              <div className="relative z-10">
                <div className="flex items-center mb-8">
                  <div className="relative p-4 rounded-2xl bg-[#161616] border border-white/10 shadow-2xl">
                    <div
                      className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                      style={{ background: `linear-gradient(135deg, ${s.color}33, transparent)` }}
                    />
                    <s.icon className="w-7 h-7 relative" style={{ color: s.color }} />
                  </div>
                  {i < 2 && (
                    <div className="h-px flex-grow bg-gradient-to-r from-white/10 to-transparent ml-6 hidden md:block" />
                  )}
                </div>
                <h3 className="text-2xl font-semibold mb-3 tracking-tight group-hover:translate-x-1 transition-transform duration-300">
                  {s.title}
                </h3>
                <p className="text-[#9ca3af] leading-relaxed text-[15px]">{s.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>


      {/* Why Engram */}
      <section id="why" className="relative px-8 py-24 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div>
            <div className="text-xs uppercase tracking-widest text-[#06b6d4] mb-3">Why Engram</div>
            <h2 className="text-4xl md:text-5xl font-semibold mb-6">Not search.<br />Memory.</h2>
            <p className="text-[#6b7280] leading-relaxed text-lg mb-4">
              Traditional RAG retrieves chunks of text by similarity. It finds passages — not understanding.
            </p>
            <p className="text-[#6b7280] leading-relaxed text-lg">
              Engram builds a graph of the concepts, people, projects, and ideas across everything you read and write. When you ask a question, it traverses connections — the way you actually remember.
            </p>
          </div>
          <div className="card-engram p-8 aspect-square flex items-center justify-center">
            <GraphMock />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-12 border-t border-[#1f1f1f] mt-12">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-[#6b7280]">
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

function GraphMock() {
  const nodes = [
    { x: 200, y: 50, r: 14, c: "#7c3aed", label: "Claude" },
    { x: 80, y: 140, r: 10, c: "#06b6d4", label: "RAG" },
    { x: 320, y: 130, r: 12, c: "#06b6d4", label: "Notion" },
    { x: 200, y: 200, r: 18, c: "#7c3aed", label: "You" },
    { x: 60, y: 290, r: 10, c: "#7c3aed", label: "Medium" },
    { x: 340, y: 280, r: 11, c: "#06b6d4", label: "Drive" },
    { x: 200, y: 350, r: 12, c: "#7c3aed", label: "Graph" },
  ];
  const edges: [number, number][] = [[0,3],[1,3],[2,3],[3,4],[3,5],[3,6],[0,2],[1,4],[5,6]];
  return (
    <svg viewBox="0 0 400 400" className="w-full h-full">
      {edges.map(([a,b], i) => (
        <line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} stroke="#1f1f1f" strokeWidth="1" />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r + 8} fill={n.c} opacity="0.15" />
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.c} />
          <text x={n.x} y={n.y + n.r + 16} textAnchor="middle" fill="#6b7280" fontSize="10" fontFamily="Poppins">{n.label}</text>
        </g>
      ))}
    </svg>
  );
}
