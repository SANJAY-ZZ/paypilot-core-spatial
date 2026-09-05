import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api, AuditEvent } from "@/lib/api";
import {
  Activity,
  X,
  Shield,
  Bot,
  Zap,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowUpRight,
  RefreshCw,
} from "lucide-react";

export function ActivityPanel({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const navigate = useNavigate();

  const { data: auditData, isLoading, refetch } = useQuery({
    queryKey: ["audit-panel"],
    queryFn: () => api.getAuditTrail({ limit: 20 }),
    enabled: isOpen,
    refetchInterval: isOpen ? 10000 : false,
  });

  if (!isOpen) return null;

  const eventBadge: Record<string, { color: string; label: string }> = {
    OPPORTUNITY_DISCOVERED: { color: "text-blue-400 bg-blue-500/10 border-blue-500/30", label: "DISCOVERY" },
    OPPORTUNITY_ANALYZED: { color: "text-purple-400 bg-purple-500/10 border-purple-500/30", label: "ANALYSIS" },
    ACTION_PROPOSED: { color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30", label: "PROPOSED" },
    GUARDIAN_APPROVED: { color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30", label: "GUARDIAN PASS" },
    GUARDIAN_BLOCKED: { color: "text-destructive bg-destructive/10 border-destructive/30", label: "GUARDIAN BLOCK" },
    MERCHANT_APPROVED: { color: "text-amber-400 bg-amber-500/10 border-amber-500/30", label: "AUTHORIZED" },
    EXECUTION_STARTED: { color: "text-accent bg-accent/10 border-accent/30", label: "DISPATCHING" },
    EXECUTION_SUCCESS: { color: "text-emerald-400 bg-emerald-500/15 border-emerald-500/30", label: "EXECUTED" },
    PAYMENT_FAILED: { color: "text-destructive bg-destructive/10 border-destructive/30", label: "FAILED" },
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex justify-end bg-background/60 backdrop-blur-sm animate-fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md bg-card/95 border-l border-border h-full flex flex-col backdrop-blur-2xl shadow-2xl"
      >
        {/* Panel Header */}
        <div className="p-5 border-b border-border/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Activity className="h-4 w-4 text-accent" />
            <div>
              <h3 className="font-mono text-xs tracking-wider text-foreground font-semibold">
                SYSTEM ACTIVITY STREAM
              </h3>
              <p className="font-mono text-[9px] text-muted-foreground">
                Real-time multi-agent audit telemetry
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="p-1 text-muted-foreground hover:text-foreground rounded border border-border/40 transition-colors"
              title="Refresh Activity"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={onClose}
              className="p-1 text-muted-foreground hover:text-foreground rounded border border-border/40 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Stream List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-24 space-y-3">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              <span className="font-mono text-[10px] text-muted-foreground tracking-wider">
                SYNCHRONIZING ACTIVITY...
              </span>
            </div>
          ) : !auditData || auditData.items.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground font-mono text-xs">
              No recent activity recorded yet.
            </div>
          ) : (
            auditData.items.map((event: AuditEvent) => {
              const badge = eventBadge[event.event_type] || {
                color: "text-muted-foreground bg-secondary border-border",
                label: event.event_type,
              };
              return (
                <div
                  key={event.id}
                  onClick={() => {
                    onClose();
                    navigate({ to: "/audit" });
                  }}
                  className="p-3 bg-secondary/30 hover:bg-secondary/60 border border-border/40 rounded-lg transition-all cursor-pointer space-y-2 group"
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className={`px-2 py-0.5 rounded border text-[8px] font-semibold uppercase ${badge.color}`}>
                      {badge.label}
                    </span>
                    <span className="text-muted-foreground">
                      {new Date(event.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>

                  <p className="text-xs text-foreground font-sans leading-snug group-hover:text-accent transition-colors">
                    {event.reason}
                  </p>

                  <div className="flex items-center justify-between text-[9px] font-mono text-muted-foreground/80 pt-1 border-t border-border/20">
                    <span>Agent: {event.agent}</span>
                    <span className="text-accent flex items-center gap-0.5">
                      VIEW IN AUDIT <ArrowUpRight className="h-2.5 w-2.5" />
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Panel Footer */}
        <div className="p-4 border-t border-border/40 bg-secondary/20 flex items-center justify-between">
          <button
            onClick={() => {
              onClose();
              navigate({ to: "/audit" });
            }}
            className="w-full text-center py-2 bg-accent/15 hover:bg-accent/25 border border-accent/40 text-accent font-mono text-xs rounded font-medium transition-colors"
          >
            VIEW COMPLETE AUDIT TRAIL
          </button>
        </div>
      </div>
    </div>
  );
}
