import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api } from "@/lib/api";
import {
  ArrowLeft,
  Bot,
  Sparkles,
  Shield,
  Play,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Zap,
} from "lucide-react";

export const Route = createFileRoute("/copilot")({
  head: () => ({
    meta: [
      { title: "AI COPILOT — PayPilot" },
      { name: "description", content: "Operational AI Revenue Copilot for Merchants." },
    ],
  }),
  component: CopilotView,
});

function CopilotView() {
  const queryClient = useQueryClient();
  const [selectedOppId, setSelectedOppId] = useState<string | null>(null);

  const { data: opportunities, isLoading } = useQuery({
    queryKey: ["opportunities"],
    queryFn: () => api.getOpportunities(),
  });

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });

  // Top prioritized opportunity
  const topOpp = opportunities?.items?.[0];

  const previewMutation = useMutation({
    mutationFn: (oppId: string) => api.previewAction({ opportunity_id: oppId }),
  });

  const executeMutation = useMutation({
    mutationFn: (actionId: string) =>
      api.executeAction({
        action_id: actionId,
        idempotency_key: `copilot_exec_${actionId}_${Date.now()}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["actions"] });
    },
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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">AI COPILOT</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-accent/10 border border-accent/30 rounded font-mono text-[10px] text-accent">
            <Bot className="h-3.5 w-3.5" />
            <span>AI REASONING ENGINE ACTIVE</span>
          </div>
        </div>

        {/* Title */}
        <div className="mb-8">
          <div className="flex items-center gap-2 font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
            <span>OPERATIONAL REVENUE INTELLIGENCE</span>
          </div>
          <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
            AI Revenue Copilot
          </h1>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              COPILOT SYNTHESIZING SYSTEM OPPORTUNITIES...
            </p>
          </div>
        ) : !topOpp ? (
          <div className="border border-border/40 bg-card/20 rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-muted-foreground">No active opportunities detected for Copilot.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Copilot Strategy Card */}
            <div className="lg:col-span-2 space-y-6">
              <div className="border border-accent/40 bg-card/60 rounded-xl p-6 backdrop-blur-md relative overflow-hidden space-y-6">
                <div className="absolute top-0 right-0 w-48 h-48 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 font-mono text-xs text-accent font-semibold tracking-wider uppercase">
                    <Sparkles className="h-4 w-4" /> HIGHEST-VALUE STRATEGIC OPPORTUNITY
                  </span>
                  <span className="px-2 py-0.5 rounded font-mono text-[9px] bg-secondary border border-border text-muted-foreground uppercase">
                    {topOpp.type.replace(/_/g, " ")}
                  </span>
                </div>

                <div>
                  <h2 className="font-display text-3xl text-foreground font-medium">{topOpp.title}</h2>
                  <div className="mt-3 flex items-baseline gap-3">
                    <span className="font-mono text-4xl text-accent font-bold">
                      ₹{topOpp.potential_revenue.toLocaleString("en-IN")}
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">Immediate Recoverable Liquidity</span>
                  </div>
                </div>

                {/* Copilot Reasoning Box */}
                <div className="p-4 bg-secondary/40 border border-border/60 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-muted-foreground tracking-wider">
                      COPILOT SYNTHESIS:
                    </span>
                    <span className="font-mono text-[9px] text-emerald-400">
                      Model Confidence: {(topOpp.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-foreground leading-relaxed">
                    {topOpp.reasoning || topOpp.reason}
                  </p>
                </div>

                {/* Key Factors */}
                {topOpp.key_factors && topOpp.key_factors.length > 0 && (
                  <div className="space-y-2">
                    <span className="font-mono text-[10px] text-muted-foreground tracking-wider block">
                      CORE OPERATIONAL DRIVERS:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {topOpp.key_factors.map((f, i) => (
                        <div key={i} className="p-2.5 bg-card/60 border border-border/40 rounded text-xs font-mono text-muted-foreground">
                          {f}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Trigger Banner */}
                <div className="pt-4 border-t border-border/40 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <Shield className="h-5 w-5 text-emerald-400" />
                    <div>
                      <span className="font-mono text-xs text-foreground font-medium block">
                        Guardian Policy Pre-verified
                      </span>
                      <span className="font-mono text-[10px] text-muted-foreground">
                        Estimated exposure ₹0.00 • Autonomous Execution Allowed
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => previewMutation.mutate(topOpp.id)}
                    disabled={previewMutation.isPending}
                    className="w-full sm:w-auto px-6 py-2.5 bg-accent text-accent-foreground font-mono text-xs rounded font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    {previewMutation.isPending ? "GUARDIAN EVALUATING..." : "RUN STRATEGY NOW"}
                  </button>
                </div>

                {/* Preview Result */}
                {previewMutation.data && (
                  <div className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-emerald-400 font-semibold">
                        GUARDIAN: {previewMutation.data.guardian_result.decision.toUpperCase()}
                      </span>
                      <button
                        onClick={() => executeMutation.mutate(previewMutation.data!.action_id)}
                        disabled={executeMutation.isPending}
                        className="px-4 py-1.5 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90"
                      >
                        {executeMutation.isPending ? "DISPATCHING..." : "DISPATCH VIA RAZORPAY"}
                      </button>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono">
                      {previewMutation.data.guardian_result.reason}
                    </p>
                  </div>
                )}

                {/* Execution Result */}
                {executeMutation.data && (
                  <div className="mt-4 p-4 bg-emerald-500/15 border border-emerald-500/40 rounded-lg text-xs font-mono space-y-2">
                    <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4" /> REVENUE ACTION EXECUTED
                    </div>
                    {executeMutation.data.execution_result?.short_url && (
                      <div>
                        Payment Link:{" "}
                        <a
                          href={executeMutation.data.execution_result.short_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent underline"
                        >
                          {executeMutation.data.execution_result.short_url}
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar: Pipeline & Next Queue */}
            <div className="space-y-6">
              <div className="border border-border/60 bg-card/30 rounded-xl p-5 space-y-4">
                <h3 className="font-mono text-xs tracking-wider text-foreground">
                  COPILOT REVENUE RADAR
                </h3>
                <div className="space-y-3">
                  {(opportunities?.items || []).slice(1, 5).map((opp) => (
                    <div
                      key={opp.id}
                      className="p-3 bg-secondary/20 hover:bg-secondary/40 border border-border/40 rounded-lg transition-colors space-y-1"
                    >
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-foreground truncate max-w-[150px]">{opp.title}</span>
                        <span className="text-accent font-semibold">
                          ₹{opp.potential_revenue.toLocaleString("en-IN")}
                        </span>
                      </div>
                      <div className="flex justify-between text-[9px] font-mono text-muted-foreground">
                        <span>{opp.type.replace(/_/g, " ")}</span>
                        <span className="text-emerald-400">{(opp.confidence * 100).toFixed(0)}% match</span>
                      </div>
                    </div>
                  ))}
                </div>

                <Link
                  to="/opportunities"
                  className="block text-center font-mono text-[10px] text-accent hover:underline pt-2"
                >
                  VIEW ALL 27 OPPORTUNITIES →
                </Link>
              </div>
            </div>
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
