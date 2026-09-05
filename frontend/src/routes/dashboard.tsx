import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api } from "@/lib/api";
import {
  ArrowLeft,
  TrendingUp,
  Users,
  AlertCircle,
  Sparkles,
  Shield,
  Zap,
  ArrowUpRight,
  RefreshCw,
} from "lucide-react";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "REVENUE COMMAND — PayPilot" },
      { name: "description", content: "Real-time revenue command and analytical overview." },
    ],
  }),
  component: DashboardView,
});

function DashboardView() {
  const { data: dashboard, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });

  return (
    <ApplicationShell>
      <main className="min-h-screen pt-20 pb-16 px-8 max-w-[1600px] mx-auto">
        {/* Top Breadcrumb & Status */}
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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">REVENUE COMMAND</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="font-mono text-[10px] tracking-[0.25em] text-muted-foreground">
                BACKEND SYNCHRONIZED
              </span>
            </div>
            <button
              onClick={() => refetch()}
              className="p-1.5 rounded border border-border/50 text-muted-foreground hover:text-foreground transition-colors"
              title="Refresh Data"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              SYNCHRONIZING REVENUE TELEMETRY...
            </p>
          </div>
        ) : isError || !dashboard ? (
          <div className="border border-destructive/40 bg-destructive/5 rounded-lg p-8 text-center my-12">
            <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-3" />
            <h3 className="font-mono text-sm tracking-wider text-foreground mb-2">TELEMETRY SYNC FAILED</h3>
            <p className="text-sm text-muted-foreground mb-4">Could not connect to the PayPilot backend service.</p>
            <button
              onClick={() => refetch()}
              className="font-mono text-xs px-4 py-2 bg-accent text-accent-foreground rounded hover:opacity-90 transition-opacity"
            >
              RETRY CONNECTION
            </button>
          </div>
        ) : (
          <div className="space-y-10">
            {/* Title Section */}
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground">
                  MERCHANT ECOSYSTEM
                </span>
                <span className="h-px w-8 bg-border" />
                <span className="font-mono text-[10px] tracking-[0.2em] text-accent">
                  {dashboard.merchant_name} ({dashboard.currency})
                </span>
              </div>
              <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
                Revenue Intelligence Command
              </h1>
            </div>

            {/* Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="border border-border/60 bg-card/40 rounded-lg p-5 backdrop-blur-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-accent/5 rounded-full blur-2xl pointer-events-none" />
                <div className="flex items-center justify-between text-muted-foreground mb-3">
                  <span className="font-mono text-[10px] tracking-[0.25em]">TOTAL GROSS REVENUE</span>
                  <TrendingUp className="h-4 w-4 text-accent" />
                </div>
                <div className="font-mono text-2xl lg:text-3xl text-foreground font-medium">
                  ₹{dashboard.total_revenue.toLocaleString("en-IN")}
                </div>
                <div className="mt-2 flex items-center gap-2 font-mono text-[10px] text-emerald-400">
                  <span>+14.2%</span>
                  <span className="text-muted-foreground">vs previous cycle</span>
                </div>
              </div>

              <div className="border border-border/60 bg-card/40 rounded-lg p-5 backdrop-blur-sm relative overflow-hidden">
                <div className="flex items-center justify-between text-muted-foreground mb-3">
                  <span className="font-mono text-[10px] tracking-[0.25em]">ACTIVE CUSTOMERS</span>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="font-mono text-2xl lg:text-3xl text-foreground font-medium">
                  {dashboard.customer_count.toLocaleString("en-IN")}
                </div>
                <div className="mt-2 flex items-center gap-2 font-mono text-[10px] text-emerald-400">
                  <span>+8.7%</span>
                  <span className="text-muted-foreground">retention affinity</span>
                </div>
              </div>

              <div className="border border-accent/40 bg-accent/5 rounded-lg p-5 backdrop-blur-sm relative overflow-hidden">
                <div className="flex items-center justify-between text-accent mb-3">
                  <span className="font-mono text-[10px] tracking-[0.25em]">RECOVERABLE CASHFLOW</span>
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="font-mono text-2xl lg:text-3xl text-accent font-medium">
                  ₹{dashboard.recoverable_revenue.toLocaleString("en-IN")}
                </div>
                <div className="mt-2 flex items-center gap-2 font-mono text-[10px] text-accent/80">
                  <span>{dashboard.recovery_rate}%</span>
                  <span className="text-muted-foreground">historical recovery rate</span>
                </div>
              </div>

              <div className="border border-border/60 bg-card/40 rounded-lg p-5 backdrop-blur-sm relative overflow-hidden">
                <div className="flex items-center justify-between text-muted-foreground mb-3">
                  <span className="font-mono text-[10px] tracking-[0.25em]">AI OPPORTUNITIES</span>
                  <Zap className="h-4 w-4 text-amber-400" />
                </div>
                <div className="font-mono text-2xl lg:text-3xl text-foreground font-medium">
                  {dashboard.opportunity_count}
                </div>
                <div className="mt-2 flex items-center gap-2 font-mono text-[10px] text-amber-400/80">
                  <span>{dashboard.ai_actions_today} actions</span>
                  <span className="text-muted-foreground">executed today</span>
                </div>
              </div>
            </div>

            {/* Opportunity Breakdown & Recent Stream */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Category Breakdown */}
              <div className="border border-border/60 bg-card/30 rounded-lg p-6 lg:col-span-1">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-mono text-xs tracking-[0.28em] text-foreground">OPPORTUNITY DYNAMICS</h3>
                  <Link
                    to="/opportunities"
                    className="font-mono text-[10px] text-accent hover:underline flex items-center gap-1"
                  >
                    EXPLORE <ArrowUpRight className="h-3 w-3" />
                  </Link>
                </div>

                <div className="space-y-5">
                  {dashboard.opportunity_breakdown.map((item) => {
                    const totalPot = dashboard.opportunity_breakdown.reduce(
                      (acc, cur) => acc + cur.potential_revenue,
                      0
                    );
                    const pct = totalPot > 0 ? (item.potential_revenue / totalPot) * 100 : 0;
                    return (
                      <div key={item.type} className="space-y-1.5">
                        <div className="flex justify-between font-mono text-xs">
                          <span className="text-muted-foreground">{item.label}</span>
                          <span className="text-foreground font-medium">
                            ₹{item.potential_revenue.toLocaleString("en-IN")}
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-border/40 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent rounded-full"
                            style={{ width: `${Math.max(5, pct)}%` }}
                          />
                        </div>
                        <div className="flex justify-between font-mono text-[9px] text-muted-foreground/70">
                          <span>{item.count} opportunities</span>
                          <span>{pct.toFixed(1)}% of pool</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* High Priority Actions Stream */}
              <div className="border border-border/60 bg-card/30 rounded-lg p-6 lg:col-span-2 space-y-4">
                <div className="flex items-center justify-between border-b border-border/40 pb-4">
                  <div>
                    <h3 className="font-mono text-xs tracking-[0.28em] text-foreground">
                      AUTONOMOUS AGENT ACTIONS
                    </h3>
                    <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
                      Strategist propositions governed by Guardian policy
                    </p>
                  </div>
                  <Link
                    to="/actions"
                    className="font-mono text-[10px] text-accent hover:underline flex items-center gap-1"
                  >
                    ALL ACTIONS <ArrowUpRight className="h-3 w-3" />
                  </Link>
                </div>

                {dashboard.recent_actions.length === 0 ? (
                  <div className="py-12 text-center text-muted-foreground font-mono text-xs">
                    No actions generated yet. Launch a preview from Opportunities.
                  </div>
                ) : (
                  <div className="divide-y divide-border/30">
                    {dashboard.recent_actions.map((act) => (
                      <div key={act.id} className="py-3.5 flex items-center justify-between gap-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-foreground font-medium">
                              {act.action_type.replace(/_/g, " ").toUpperCase()}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-wider ${
                                act.status === "executed"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                  : act.status === "approved"
                                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                                  : act.status === "blocked"
                                  ? "bg-destructive/10 text-destructive border border-destructive/30"
                                  : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                              }`}
                            >
                              {act.status}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Agent: {act.agent} • Confidence: {(act.confidence * 100).toFixed(0)}%
                          </p>
                        </div>

                        <div className="text-right">
                          <div className="font-mono text-xs text-foreground">
                            {act.execution_result?.reference_id || act.idempotency_key || act.id}
                          </div>
                          <div className="font-mono text-[10px] text-muted-foreground">
                            {new Date(act.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
