import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, CommerceReadinessResponse } from "@/lib/api";
import {
  ArrowLeft,
  Sparkles,
  Bot,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ShoppingBag,
  Cpu,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

export const Route = createFileRoute("/commerce")({
  head: () => ({
    meta: [
      { title: "AI COMMERCE — PayPilot" },
      { name: "description", content: "Agentic commerce and autonomous buyer readiness." },
    ],
  }),
  component: CommerceView,
});

function CommerceView() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["commerce-readiness"],
    queryFn: () => api.getCommerceReadiness(),
  });

  return (
    <ApplicationShell>
      <main className="min-h-screen pt-20 pb-16 px-8 max-w-[1600px] mx-auto">
        {/* Top Breadcrumb */}
        <div className="flex items-center justify-between border-b border-border/40 pb-6 mb-8">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              search={{ state: "active" }}
              className="inline-flex items-center gap-2 font-mono text-[11px] tracking-[0.32em] text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.5} />
              CORE
            </Link>
            <span className="text-border">/</span>
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">AI COMMERCE</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-accent/10 border border-accent/30 rounded font-mono text-[10px] text-accent">
            <Bot className="h-3.5 w-3.5" />
            <span>AGENTIC COMMERCE PROTOCOL</span>
          </div>
        </div>

        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between mb-8 gap-6">
          <div>
            <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
              AUTONOMOUS BUYER AGENT COMPATIBILITY
            </div>
            <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
              Commerce Readiness
            </h1>
            <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
              Evaluates how effectively your catalog, APIs, pricing clarity, and checkout flows can be discovered and transacted by autonomous AI agents.
            </p>
          </div>

          {data && (
            <div className="flex items-center gap-6 border border-border/60 bg-card/40 rounded-xl px-6 py-4 backdrop-blur-sm">
              <div>
                <div className="font-mono text-[9px] tracking-[0.25em] text-muted-foreground">READINESS SCORE</div>
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-3xl text-accent font-bold">{data.overall_score}</span>
                  <span className="font-mono text-xs text-muted-foreground">/ 100</span>
                </div>
              </div>
              <div className="h-10 w-px bg-border/60" />
              <div>
                <div className="font-mono text-[9px] tracking-[0.25em] text-muted-foreground">GRADE</div>
                <div className="font-mono text-3xl text-emerald-400 font-bold">{data.grade}</div>
              </div>
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              CALCULATING AGENTIC COMMERCE VECTORS...
            </p>
          </div>
        ) : !data ? (
          <div className="border border-border/40 bg-card/20 rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-muted-foreground">Readiness telemetry unavailable.</p>
          </div>
        ) : (
          <div className="space-y-10">
            {/* Category Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {data.categories.map((cat, idx) => (
                <div
                  key={idx}
                  className="border border-border/60 bg-card/40 rounded-xl p-5 backdrop-blur-sm space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-foreground font-semibold tracking-wide">
                        {cat.category}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[9px] font-mono uppercase ${
                          cat.score >= 90
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : cat.score >= 70
                            ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                            : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                        }`}
                      >
                        {cat.score}/100
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground leading-relaxed font-sans">{cat.details}</p>
                  </div>

                  <div className="space-y-1.5 pt-3 border-t border-border/30">
                    <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full"
                        style={{ width: `${cat.score}%` }}
                      />
                    </div>
                    <div className="flex justify-between font-mono text-[9px] text-muted-foreground">
                      <span>Weight: {(cat.weight * 100).toFixed(0)}%</span>
                      <span className="capitalize">{cat.status.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Recommendations Section */}
            <div className="border border-border/60 bg-card/30 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center justify-between border-b border-border/40 pb-3">
                <h3 className="font-mono text-xs tracking-wider text-foreground">
                  AI AGENT OPTIMIZATION RECOMMENDATIONS
                </h3>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {data.recommendations.length} Actionable Items
                </span>
              </div>

              <div className="divide-y divide-border/30">
                {data.recommendations.map((rec) => (
                  <div key={rec.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[8px] font-mono uppercase tracking-wider font-semibold ${
                            rec.impact === "high"
                              ? "bg-destructive/15 text-destructive border border-destructive/30"
                              : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                          }`}
                        >
                          {rec.impact} IMPACT
                        </span>
                        <span className="font-mono text-xs text-foreground font-medium">{rec.title}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{rec.description}</p>
                    </div>

                    <Link
                      to="/opportunities"
                      className="px-3.5 py-1.5 bg-secondary hover:bg-secondary/80 border border-border/60 text-foreground font-mono text-xs rounded transition-colors whitespace-nowrap self-start sm:self-auto"
                    >
                      RESOLVE IN PIPELINE
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
