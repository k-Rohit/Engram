import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, ArrowUpRight } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Engram — the archive of everything you've figured out" },
      { name: "description", content: "Engram reads your Claude Code sessions, Notion notes and AI newsletters, distills what mattered, and connects it into one knowledge graph — so every answer comes back with sources." },
      { property: "og:title", content: "Engram — the archive of everything you've figured out" },
      { property: "og:description", content: "One knowledge graph across your code sessions, notes and reading. Answers with receipts." },
    ],
  }),
  component: Landing,
});

const SOURCES = [
  {
    num: "01",
    name: "Claude Code",
    desc: "Debugging sessions, decisions, and every question you asked — cleaned of tool noise, distilled into atomic insight cards.",
    stat: "10 sessions → 264 cards",
  },
  {
    num: "02",
    name: "Notion",
    desc: "Project notes and write-ups, kept verbatim — your own words, never paraphrased away.",
    stat: "7 pages",
  },
  {
    num: "03",
    name: "Gmail",
    desc: "The AI and engineering newsletters you actually read, pulled straight from your inbox.",
    stat: "54 issues",
  },
];

const STEPS = [
  {
    num: "01",
    title: "Distill",
    body: "Raw transcripts are ~90% tool noise. Engram strips it and keeps the problems, the fixes, and the concepts you asked about.",
  },
  {
    num: "02",
    title: "Connect",
    body: "Everything lands in one Cognee knowledge graph — so a newsletter you read links to a bug you fixed three weeks later.",
  },
  {
    num: "03",
    title: "Recall",
    body: "Ask in plain language, follow up like a conversation. Every answer is traced back to the exact sources it came from.",
  },
];

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* Nav */}
      <nav className="border-b border-border">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="t-label !text-foreground flex items-center gap-2.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber pulse-dot" />
            Engram
          </span>
          <div className="flex items-center gap-7">
            <a href="#sources" className="t-label hover:!text-foreground transition-colors hidden sm:block">Sources</a>
            <a href="#method" className="t-label hover:!text-foreground transition-colors hidden sm:block">Method</a>
            <Link to="/app" className="btn-amber px-4 py-2">
              Open the archive
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="max-w-5xl mx-auto px-6 pt-24 pb-16">
        <p className="t-label mb-8">A private archive of everything you've figured out</p>
        <h1 className="font-display text-[3.4rem] md:text-[5rem] leading-[1.02] text-foreground max-w-4xl">
          You've already solved this.
          <br />
          <em className="text-amber">Ask again.</em>
        </h1>
        <p className="mt-8 text-lg text-muted-foreground leading-relaxed max-w-xl">
          Engram reads your Claude Code sessions, Notion notes and AI newsletters, distills
          what mattered, and connects it into one knowledge graph — so every answer comes
          back with sources.
        </p>
        <div className="mt-10 flex items-center gap-4">
          <Link to="/app" className="btn-amber px-5 py-2.5 inline-flex items-center gap-2">
            Ask your archive <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <a href="#method" className="btn-line px-5 py-2.5">How it works</a>
        </div>
      </header>

      {/* Specimen: a real archive entry */}
      <section className="max-w-5xl mx-auto px-6 pb-24">
        <div className="card-arc">
          <div className="px-5 py-3 border-b border-border flex items-center justify-between">
            <span className="t-label">Entry — retrieved from memory</span>
            <span className="t-label !text-amber">2 sources</span>
          </div>
          <div className="p-6 md:p-8 grid md:grid-cols-[1fr_1.4fr] gap-8">
            <div>
              <p className="t-label mb-3">You asked</p>
              <p className="font-display text-2xl md:text-[1.7rem] leading-snug text-foreground">
                “What did I decide about running the Docker services?”
              </p>
            </div>
            <div className="md:border-l md:border-border md:pl-8">
              <p className="t-label mb-3">Engram remembers</p>
              <p className="text-[0.95rem] leading-relaxed text-foreground/85">
                You trimmed <span className="text-amber">docker-compose</span> down to the
                services you actually need — Postgres and Airflow — and dropped Langfuse and
                ClickHouse to cut RAM. The command you settled on was{" "}
                <code className="font-mono text-[0.82em] bg-amber/10 text-[#e6c184] px-1.5 py-0.5 rounded-[3px]">
                  docker compose up -d --build postgres airflow
                </code>
                .
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                <span className="stamp !text-amber !border-amber/40">src: claude_code</span>
                <span className="stamp">src: notion</span>
                <span className="stamp">project: arxiv_paper_curator</span>
              </div>
            </div>
          </div>
        </div>
        <p className="mt-3 t-label !normal-case !tracking-normal text-center">
          — an actual answer from the author's archive —
        </p>
      </section>

      {/* Sources index */}
      <section id="sources" className="border-t border-border">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="flex items-baseline justify-between mb-12">
            <h2 className="font-display text-4xl md:text-5xl">What goes in</h2>
            <span className="t-label hidden md:block">The index</span>
          </div>
          <div className="divide-y divide-border border-y border-border">
            {SOURCES.map((s) => (
              <div key={s.num} className="py-7 grid grid-cols-[3rem_1fr] md:grid-cols-[4rem_14rem_1fr_auto] gap-4 items-baseline group">
                <span className="font-mono text-sm text-amber">{s.num}</span>
                <h3 className="font-display text-2xl text-foreground">{s.name}</h3>
                <p className="col-start-2 md:col-start-3 text-[0.95rem] text-muted-foreground leading-relaxed max-w-lg">
                  {s.desc}
                </p>
                <span className="col-start-2 md:col-start-4 t-label !text-foreground/60 whitespace-nowrap">{s.stat}</span>
              </div>
            ))}
          </div>
          <p className="mt-6 t-label">
            Every entry keeps its provenance — source, project, session.
          </p>
        </div>
      </section>

      {/* Method */}
      <section id="method" className="border-t border-border">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="flex items-baseline justify-between mb-12">
            <h2 className="font-display text-4xl md:text-5xl">How it answers</h2>
            <span className="t-label hidden md:block">The method</span>
          </div>
          <div className="grid md:grid-cols-3 gap-px bg-border border border-border">
            {STEPS.map((s) => (
              <div key={s.num} className="bg-background p-7">
                <span className="font-mono text-sm text-amber">{s.num}</span>
                <h3 className="font-display text-2xl mt-4 mb-3">{s.title}</h3>
                <p className="text-[0.95rem] text-muted-foreground leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>

          {/* the "not search, memory" argument as a footnote */}
          <div className="mt-12 grid md:grid-cols-[4rem_1fr] gap-4">
            <span className="t-label pt-1">Note</span>
            <p className="font-display text-xl md:text-2xl leading-relaxed text-foreground/85 max-w-3xl">
              Search finds documents. Memory connects them. A vector database retrieves the
              nearest paragraph — a knowledge graph walks from the article you read, to the
              concept it taught you, to the decision you made because of it.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border">
        <div className="max-w-5xl mx-auto px-6 py-24 text-center">
          <p className="t-label mb-6">Stop re-deriving what you already know</p>
          <h2 className="font-display text-4xl md:text-6xl leading-tight">
            Your archive is <em className="text-amber">already written.</em>
          </h2>
          <Link to="/app" className="btn-amber px-6 py-3 mt-10 inline-flex items-center gap-2">
            Open the archive <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="max-w-5xl mx-auto px-6 py-8 flex items-center justify-between">
          <span className="t-label">Engram — built on Cognee</span>
          <span className="t-label">© 2026</span>
        </div>
      </footer>
    </div>
  );
}
