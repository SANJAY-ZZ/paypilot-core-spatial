import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, AuditEvent } from "@/lib/api";
import {
  ArrowLeft,
  Shield,
  FileText,
  Filter,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  RefreshCw,
} from "lucide-react";

export const Route = createFileRoute("/audit")({
  head: () => ({
    meta: [
      { title: "AUDIT — PayPilot" },
      { name: "description", content: "Immutable audit trail and agent decision log." },
    ],
  }),
  component: AuditView,
});

function AuditView() {
  const [agentFilter, setAgentFilter] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["audit", agentFilter],
    queryFn: () =>
      api.getAuditTrail({
        agent: agentFilter === "ALL" ? undefined : agentFilter.toLowerCase(),
        limit: 50,
      }),
  });

  const eventTypeColors: Record<string, string> = {
    OPPORTUNITY_DISCOVERED: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    OPPORTUNITY_ANALYZED: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    ACTION_PROPOSED: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    GUARDIAN_APPROVED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    GUARDIAN_BLOCKED: "bg-destructive/10 text-destructive border-destructive/30",
    MERCHANT_APPROVED: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    EXECUTION_STARTED: "bg-accent/10 text-accent border-accent/30",
    EXECUTION_SUCCESS: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    EXECUTION_FAILED: "bg-destructive/10 text-destructive border-destructive/30",
    PAYMENT_FAILED: "bg-destructive/10 text-destructive border-destructive/30",
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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">AUDIT</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-secondary border border-border/60 rounded font-mono text-[10px] text-muted-foreground">
            <Shield className="h-3.5 w-3.5 text-accent" />
            <span>IMMUTABLE LEDGER / 100% TRACEABLE</span>
          </div>
        </div>

        {/* Title */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
              CHRONOLOGICAL COMPLIANCE STREAM
            </div>
            <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
              Audit Trail
            </h1>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 font-mono text-xs">
            {["ALL", "SCOUT", "ANALYST", "STRATEGIST", "GUARDIAN", "EXECUTOR", "MERCHANT", "AUDITOR"].map(
              (ag) => (
                <button
                  key={ag}
                  onClick={() => setAgentFilter(ag)}
                  className={`px-3 py-1.5 rounded text-[10px] uppercase whitespace-nowrap transition-all ${
                    agentFilter === ag
                      ? "bg-accent text-accent-foreground font-semibold"
                      : "bg-secondary/40 text-muted-foreground hover:text-foreground border border-border/40"
                  }`}
                >
                  {ag}
                </button>
              )
            )}
          </div>
        </div>

        {/* Audit Trail List */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              QUERYING IMMUTABLE AUDIT LOGS...
            </p>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="border border-border/40 bg-card/20 rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-muted-foreground">No audit entries found for selected filter.</p>
          </div>
        ) : (
          <div className="border border-border/60 bg-card/30 rounded-xl overflow-hidden backdrop-blur-sm divide-y divide-border/30">
            {data.items.map((event) => {
              const isExpanded = expandedId === event.id;
              return (
                <div key={event.id} className="p-4 hover:bg-secondary/20 transition-colors">
                  <div
                    onClick={() => setExpandedId(isExpanded ? null : event.id)}
                    className="flex flex-col md:flex-row md:items-center justify-between gap-3 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <button className="text-muted-foreground">
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </button>

                      <span
                        className={`px-2.5 py-0.5 rounded text-[9px] font-mono uppercase tracking-wider font-semibold border ${
                          eventTypeColors[event.event_type] || "bg-secondary text-muted-foreground border-border"
                        }`}
                      >
                        {event.event_type.replace(/_/g, " ")}
                      </span>

                      <span className="font-mono text-xs text-foreground font-medium">
                        [{event.agent.toUpperCase()}]
                      </span>

                      <span className="text-xs text-muted-foreground font-sans line-clamp-1">{event.reason}</span>
                    </div>

                    <div className="flex items-center gap-4 text-right font-mono text-[10px] text-muted-foreground pl-7 md:pl-0">
                      <span>{new Date(event.created_at).toLocaleString()}</span>
                      <span className="px-2 py-0.5 rounded bg-secondary text-muted-foreground text-[9px]">
                        {event.status}
                      </span>
                    </div>
                  </div>

                  {/* Expanded JSON Inspector */}
                  {isExpanded && (
                    <div className="mt-4 pl-7 pr-4 py-3 bg-secondary/30 rounded-lg border border-border/40 space-y-2">
                      <div className="flex justify-between items-center text-[10px] font-mono text-muted-foreground">
                        <span>EVENT METADATA (ID: {event.id})</span>
                        <span>ACTION ID: {event.action_id || "N/A"}</span>
                      </div>
                      <pre className="p-3 bg-card/80 rounded font-mono text-xs text-foreground/90 overflow-x-auto">
                        {JSON.stringify(event.metadata_json || {}, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
