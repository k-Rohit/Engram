import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, RefreshCw, ArrowUpRight } from "lucide-react";

const API_BASE = "http://localhost:8090";

export const Route = createFileRoute("/wall")({
  head: () => ({
    meta: [
      { title: "Engram — the stacks" },
      { name: "description", content: "Wander your archive. Rediscover what you forgot you knew." },
    ],
  }),
  component: WallPage,
});

type WallItem = {
  type: "card" | "concept";
  kind?: string;
  title: string;
  question: string;
  answer?: string;
  project?: string;
  date?: string;
};

const KIND_LABEL: Record<string, string> = {
  concept: "concept",
  problem_solution: "problem / fix",
  decision: "decision",
};

function WallPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<WallItem[] | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/wall?n=24`);
      const data = await res.json();
      setItems(data.items ?? []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // Click a memory -> hand the question to the chat and go there.
  const revisit = (item: WallItem) => {
    localStorage.setItem("engram_pending_q", item.question);
    navigate({ to: "/app" });
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top bar */}
      <header className="h-14 border-b border-border sticky top-0 bg-background/90 backdrop-blur-sm z-10">
        <div className="h-full px-6 flex items-center justify-between">
          <Link to="/" className="t-label !text-foreground flex items-center gap-2.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber pulse-dot" />
            Engram
          </Link>
          <div className="flex items-center gap-5">
            <button
              onClick={load}
              disabled={loading}
              className="t-label hover:!text-foreground transition-colors cursor-pointer flex items-center gap-1.5"
            >
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              reshuffle
            </button>
            <Link to="/app" className="btn-amber px-3 py-1.5">
              Reading room
            </Link>
          </div>
        </div>
      </header>

      {/* Intro */}
      <div className="max-w-6xl mx-auto px-6 pt-12 pb-8">
        <p className="t-label mb-4">The stacks</p>
        <h1 className="font-display text-4xl md:text-5xl leading-tight">
          Wander. You'll find something <em className="text-amber">you forgot you knew.</em>
        </h1>
        <p className="mt-4 text-sm text-muted-foreground max-w-lg leading-relaxed">
          A random shelf of your archive — questions you asked, problems you fixed, concepts
          from your reading. Click anything to revisit it in the reading room.
        </p>
      </div>

      {/* The cards */}
      <div className="max-w-6xl mx-auto px-6 pb-24">
        {!items && (
          <div className="flex items-center gap-3 py-16 justify-center">
            <Loader2 className="w-4 h-4 animate-spin text-amber" />
            <span className="t-label">Pulling from the shelves…</span>
          </div>
        )}
        {items && items.length === 0 && (
          <p className="t-label py-16 text-center">The archive is empty — or the API is down.</p>
        )}
        {items && items.length > 0 && (
          <div className="columns-1 sm:columns-2 lg:columns-3 gap-4 [column-fill:balance]">
            {items.map((item, i) => (
              <button
                key={`${item.title}-${i}`}
                onClick={() => revisit(item)}
                className="stack-card card-arc w-full text-left p-5 mb-4 break-inside-avoid cursor-pointer group"
                style={{ animationDelay: `${(i % 7) * -1.1}s` }}
              >
                <div className="flex items-center justify-between gap-3 mb-3">
                  <span className={`stamp ${item.type === "concept" ? "!text-amber !border-amber/40" : ""}`}>
                    {item.type === "concept" ? "from the graph" : KIND_LABEL[item.kind ?? ""] ?? item.kind}
                  </span>
                  {item.date && (
                    <span className="t-label">{item.date}{item.project ? ` · ${item.project}` : ""}</span>
                  )}
                </div>
                <p className="font-display text-xl leading-snug text-foreground">
                  {item.type === "concept" ? item.title : item.question || item.title}
                </p>
                {item.answer && (
                  <p className="mt-2 text-[0.85rem] text-muted-foreground leading-relaxed line-clamp-2">
                    {item.answer}
                  </p>
                )}
                <span className="mt-3 t-label flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity !text-amber">
                  revisit <ArrowUpRight className="w-3 h-3" />
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
