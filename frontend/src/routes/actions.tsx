import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, AIAction } from "@/lib/api";
import {
  ArrowLeft,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ExternalLink,
  Shield,
  Bot,
  RefreshCw,
  Copy,
  Check,
} from "lucide-react";

export const Route = createFileRoute("/actions")({
  head: () => ({
    meta: [
      { title: "EXECUTION — PayPilot" },
      { name: "description", content: "Autonomous and authorized action execution ledger." },
    ],
  }),
  component: ActionsView,
});

function ActionsView() {
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["actions"],
    queryFn: () => api.getActions({ limit: 50 }),
  });

  const approveMutation = useMutation({
    mutationFn: (actionId: string) =>
      api.approveAction({
        action_id: actionId,
        approval_notes: "Authorized by Merchant via PayPilot Execution Center",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["actions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const executeMutation = useMutation({
    mutationFn: (actionId: string) =>
      api.executeAction({
        action_id: actionId,
        idempotency_key: `act_exec_${actionId}_${Date.now()}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["actions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  const filteredItems = (data?.items || []).filter((act) => {
    if (filterStatus === "ALL") return true;
    return act.status.toLowerCase() === filterStatus.toLowerCase();
  });

  const copyUrl = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">EXECUTION</span>
          </div>

          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3 py-1 bg-secondary border border-border/60 rounded font-mono text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            REFRESH LEDGER
          </button>
        </div>

        {/* Title */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
              ACTION WORKFLOW & RAZORPAY DISPATCH
            </div>
            <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
              Execution Control Center
            </h1>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 font-mono text-xs">
            {["ALL", "EXECUTED", "AWAITING_APPROVAL", "APPROVED", "BLOCKED"].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-3 py-1.5 rounded text-[11px] whitespace-nowrap transition-all ${
                  filterStatus === st
                    ? "bg-accent text-accent-foreground font-medium"
                    : "bg-secondary/40 text-muted-foreground hover:text-foreground border border-border/40"
                }`}
              >
                {st.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Action Cards List */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              FETCHING ACTION RUNTIME STREAM...
            </p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="border border-border/40 bg-card/20 rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-muted-foreground">
              No actions found in current state. Launch a new action from Opportunities.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredItems.map((act) => (
              <div
                key={act.id}
                className="border border-border/60 bg-card/40 rounded-xl p-6 backdrop-blur-sm space-y-4 hover:border-accent/40 transition-colors"
              >
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/30 pb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider font-semibold ${
                        act.status === "executed"
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : act.status === "approved"
                          ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                          : act.status === "awaiting_approval"
                          ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                          : act.status === "blocked"
                          ? "bg-destructive/15 text-destructive border border-destructive/30"
                          : "bg-secondary text-muted-foreground border border-border"
                      }`}
                    >
                      {act.status.replace(/_/g, " ")}
                    </span>
                    <span className="font-mono text-xs text-foreground font-medium">
                      {act.action_type.replace(/_/g, " ").toUpperCase()}
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground">ID: {act.id}</span>
                  </div>

                  <div className="font-mono text-[10px] text-muted-foreground">
                    Created: {new Date(act.created_at).toLocaleString()}
                  </div>
                </div>

                {/* Body Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="p-3 bg-secondary/30 rounded border border-border/30 space-y-1">
                    <span className="text-[9px] text-muted-foreground block">AGENT & CONFIDENCE</span>
                    <div className="text-foreground">Agent: {act.agent}</div>
                    <div className="text-emerald-400">Confidence: {(act.confidence * 100).toFixed(0)}%</div>
                  </div>

                  <div className="p-3 bg-secondary/30 rounded border border-border/30 space-y-1">
                    <span className="text-[9px] text-muted-foreground block">GUARDIAN EVALUATION</span>
                    <div className="text-foreground">
                      Decision: {act.guardian_result?.decision?.toUpperCase() || "PENDING"}
                    </div>
                    <div className="text-muted-foreground truncate">{act.guardian_result?.reason}</div>
                  </div>

                  <div className="p-3 bg-secondary/30 rounded border border-border/30 space-y-1">
                    <span className="text-[9px] text-muted-foreground block">IDEMPOTENCY KEY</span>
                    <div className="text-foreground truncate">{act.idempotency_key || "NONE"}</div>
                    <div className="text-muted-foreground">Safe against duplicate execution</div>
                  </div>
                </div>

                {/* Execution Results if executed */}
                {act.execution_result && (
                  <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs font-mono space-y-2.5">
                    <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                      <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                        <CheckCircle2 className="h-4 w-4" />
                        {act.execution_result.provider === "razorpay_test"
                          ? "RAZORPAY TEST PAYMENT LINK CREATED"
                          : "RAZORPAY DISPATCH CONFIRMED"}
                      </div>
                      <span className="px-2 py-0.5 rounded text-[9px] uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        {act.execution_result.provider === "razorpay_test" ? "TEST MODE" : "MOCK MODE"}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-muted-foreground">
                      <div>
                        Reference ID: <span className="text-foreground">{act.execution_result.reference_id}</span>
                      </div>
                      <div>
                        Payment Link ID:{" "}
                        <span className="text-foreground">{act.execution_result.payment_link_id}</span>
                      </div>
                    </div>

                    {act.execution_result.short_url && (
                      <div className="flex items-center justify-between pt-2 border-t border-emerald-500/20">
                        <span className="text-muted-foreground">Payment Link:</span>
                        <div className="flex items-center gap-2">
                          <a
                            href={act.execution_result.short_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-accent/15 text-accent border border-accent/30 hover:bg-accent/25 transition-colors font-medium text-xs"
                          >
                            <span>Open Payment Link</span>
                            <ExternalLink className="h-3 w-3" />
                          </a>
                          <button
                            onClick={() => copyUrl(act.execution_result!.short_url!, act.id)}
                            className="p-1 rounded bg-secondary text-foreground hover:bg-secondary/80 border border-border/40"
                            title="Copy Link URL"
                          >
                            {copiedId === act.id ? (
                              <Check className="h-3 w-3 text-emerald-400" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  {act.status === "awaiting_approval" && (
                    <button
                      onClick={() => approveMutation.mutate(act.id)}
                      disabled={approveMutation.isPending}
                      className="px-4 py-2 bg-amber-500 text-black font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity"
                    >
                      {approveMutation.isPending ? "AUTHORIZING..." : "MERCHANT AUTHORIZE ACTION"}
                    </button>
                  )}

                  {act.status === "approved" && (
                    <button
                      onClick={() => executeMutation.mutate(act.id)}
                      disabled={executeMutation.isPending}
                      className="px-4 py-2 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                    >
                      <Play className="h-3.5 w-3.5 fill-current" />
                      {executeMutation.isPending ? "DISPATCHING..." : "DISPATCH VIA RAZORPAY"}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
