import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, Opportunity, ActionPreviewResponse, SimulationResponse, AIAction } from "@/lib/api";
import {
  ArrowLeft,
  Sparkles,
  Zap,
  Shield,
  Bot,
  Play,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  Search,
  Filter,
  X,
} from "lucide-react";

export const Route = createFileRoute("/opportunities")({
  head: () => ({
    meta: [
      { title: "OPPORTUNITIES — PayPilot" },
      { name: "description", content: "AI-discovered merchant revenue opportunities." },
    ],
  }),
  component: OpportunitiesView,
});

function OpportunitiesView() {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedOpp, setSelectedOpp] = useState<Opportunity | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["opportunities", selectedType],
    queryFn: () =>
      api.getOpportunities({
        type: selectedType === "ALL" ? undefined : selectedType,
      }),
  });

  const scanMutation = useMutation({
    mutationFn: () => api.scanOpportunities(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const filteredItems = (data?.items || []).filter((item) => {
    if (!searchQuery) return true;
    return (
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.reason.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <ApplicationShell>
      <main className="min-h-screen pt-20 pb-16 px-8 max-w-[1600px] mx-auto">
        {/* Top Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border/40 pb-6 mb-8 gap-4">
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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">OPPORTUNITIES</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => scanMutation.mutate()}
              disabled={scanMutation.isPending}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded bg-accent/10 border border-accent/40 text-accent font-mono text-xs hover:bg-accent/20 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${scanMutation.isPending ? "animate-spin" : ""}`} />
              {scanMutation.isPending ? "SCOUT SCANNING..." : "TRIGGER SCOUT SCAN"}
            </button>
          </div>
        </div>

        {/* Header & Stats Banner */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between mb-8 gap-6">
          <div>
            <div className="flex items-center gap-2 font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
              <span>UNREALISED LIQUIDITY POOL</span>
            </div>
            <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
              Revenue Opportunities
            </h1>
          </div>

          {data && (
            <div className="flex items-center gap-6 border border-border/60 bg-card/40 rounded-lg px-5 py-3.5 backdrop-blur-sm">
              <div>
                <div className="font-mono text-[9px] tracking-[0.25em] text-muted-foreground">TOTAL POOL</div>
                <div className="font-mono text-xl text-accent font-medium">
                  ₹{data.total_potential_revenue.toLocaleString("en-IN")}
                </div>
              </div>
              <div className="h-8 w-px bg-border/60" />
              <div>
                <div className="font-mono text-[9px] tracking-[0.25em] text-muted-foreground">IDENTIFIED</div>
                <div className="font-mono text-xl text-foreground font-medium">{data.total} candidates</div>
              </div>
            </div>
          )}
        </div>

        {/* Filter Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 border-b border-border/30 pb-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0">
            {[
              { id: "ALL", label: "ALL" },
              { id: "payment_recovery", label: "PAYMENT RECOVERY" },
              { id: "customer_winback", label: "CUSTOMER WIN-BACK" },
              { id: "upsell", label: "SMART UPSELL" },
              { id: "subscription_recovery", label: "SUBSCRIPTIONS" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedType(tab.id)}
                className={`px-3 py-1.5 rounded font-mono text-[11px] tracking-wider transition-all whitespace-nowrap ${
                  selectedType === tab.id
                    ? "bg-accent text-accent-foreground font-medium shadow-sm"
                    : "bg-secondary/40 text-muted-foreground hover:text-foreground border border-border/40"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative min-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search opportunity patterns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-card/40 border border-border/60 rounded text-xs font-mono placeholder:text-muted-foreground/60 text-foreground focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        {/* Opportunity Cards Grid */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              SCOUT & ANALYST AGENTS EVALUATING MERCHANDISE...
            </p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="border border-border/40 bg-card/20 rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-muted-foreground">No opportunities matching criteria.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredItems.map((opp) => (
              <OpportunityCard key={opp.id} opportunity={opp} onSelect={() => setSelectedOpp(opp)} />
            ))}
          </div>
        )}

        {/* Interactive Execution Drawer / Modal */}
        {selectedOpp && (
          <OpportunityExecutionModal opportunity={selectedOpp} onClose={() => setSelectedOpp(null)} />
        )}
      </main>
    </ApplicationShell>
  );
}

function OpportunityCard({
  opportunity,
  onSelect,
}: {
  opportunity: Opportunity;
  onSelect: () => void;
}) {
  const isLLM = opportunity.reasoning_source === "llm";
  const typeBadgeColors: Record<string, string> = {
    payment_recovery: "bg-orange-500/10 text-orange-400 border-orange-500/30",
    customer_winback: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    upsell: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    subscription_recovery: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  };

  return (
    <div className="border border-border/60 bg-card/40 hover:border-accent/50 rounded-lg p-5 backdrop-blur-sm transition-all flex flex-col justify-between group">
      <div className="space-y-4">
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2">
          <span
            className={`px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-wider border ${
              typeBadgeColors[opportunity.type] || "bg-secondary text-muted-foreground border-border"
            }`}
          >
            {opportunity.type.replace(/_/g, " ")}
          </span>

          <div className="flex items-center gap-1.5">
            {isLLM ? (
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-accent/15 border border-accent/40 font-mono text-[8px] text-accent font-medium">
                <Bot className="h-2.5 w-2.5" /> OPENAI LLM
              </span>
            ) : (
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-secondary/80 border border-border/60 font-mono text-[8px] text-muted-foreground">
                DETERMINISTIC
              </span>
            )}
          </div>
        </div>

        {/* Title & Revenue */}
        <div>
          <h3 className="font-sans font-medium text-base text-foreground group-hover:text-accent transition-colors leading-snug">
            {opportunity.title}
          </h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl text-accent font-semibold">
              ₹{opportunity.potential_revenue.toLocaleString("en-IN")}
            </span>
            <span className="font-mono text-[10px] text-muted-foreground">at risk</span>
          </div>
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-3 gap-2 py-2 border-y border-border/30 font-mono text-[10px]">
          <div>
            <span className="text-muted-foreground block text-[8px]">COHORT</span>
            <span className="text-foreground">{opportunity.affected_customer_count} buyers</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[8px]">CONFIDENCE</span>
            <span className="text-emerald-400">{(opportunity.confidence * 100).toFixed(0)}%</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[8px]">RISK</span>
            <span className="text-foreground uppercase">{opportunity.risk}</span>
          </div>
        </div>

        {/* Rationale / Evidence */}
        <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
          {opportunity.reasoning || opportunity.reason}
        </p>

        {/* Key Factors */}
        {opportunity.key_factors && opportunity.key_factors.length > 0 && (
          <div className="space-y-1 pt-1">
            {opportunity.key_factors.slice(0, 2).map((factor, idx) => (
              <div key={idx} className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground/80">
                <span className="h-1 w-1 rounded-full bg-accent" />
                <span className="truncate">{factor}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Card Footer Actions */}
      <div className="mt-5 pt-3 border-t border-border/40 flex items-center justify-between">
        <span className="font-mono text-[9px] text-muted-foreground truncate max-w-[140px]">
          {opportunity.recommended_action.replace(/_/g, " ")}
        </span>
        <button
          onClick={onSelect}
          className="px-3 py-1.5 bg-accent text-accent-foreground font-mono text-xs rounded hover:opacity-90 transition-opacity flex items-center gap-1 font-medium"
        >
          <Play className="h-3 w-3 fill-current" /> ACT
        </button>
      </div>
    </div>
  );
}

function OpportunityExecutionModal({
  opportunity,
  onClose,
}: {
  opportunity: Opportunity;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"action" | "simulate">("action");
  const [discountPercent, setDiscountPercent] = useState<number>(
    opportunity.type === "customer_winback" ? 10 : 0
  );
  const [budget, setBudget] = useState<number>(
    opportunity.type === "customer_winback" ? 3500 : 500
  );
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  // 1. Simulation Query
  const { data: simulation, isLoading: isSimulating } = useQuery({
    queryKey: [
      "simulation",
      opportunity.id,
      discountPercent,
      budget,
      opportunity.affected_customer_count,
    ],
    queryFn: () =>
      api.simulate({
        discount_percent: discountPercent,
        campaign_budget: budget,
        customer_count: opportunity.affected_customer_count,
        average_order_value: Math.round(
          opportunity.potential_revenue / Math.max(1, opportunity.affected_customer_count)
        ),
        conversion_rate: 0.25,
        duration_days: 14,
      }),
  });

  // 2. Action Preview Mutation (Strategist + Guardian)
  const previewMutation = useMutation({
    mutationFn: () =>
      api.previewAction({
        opportunity_id: opportunity.id,
        override_discount_percent: discountPercent,
        override_budget: budget,
      }),
  });

  // 3. Action Approve Mutation
  const approveMutation = useMutation({
    mutationFn: (actionId: string) =>
      api.approveAction({
        action_id: actionId,
        approval_notes: "Merchant authorized campaign from PayPilot UI.",
      }),
    onSuccess: (updated) => {
      if (previewMutation.data) {
        previewMutation.data.status = updated.status;
      }
    },
  });

  // 4. Action Execute Mutation
  const executeMutation = useMutation({
    mutationFn: (actionId: string) =>
      api.executeAction({
        action_id: actionId,
        idempotency_key: `idem_${actionId}_${Date.now()}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["actions"] });
    },
  });

  const preview = previewMutation.data;
  const execution = executeMutation.data;

  const copyPaymentUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md">
      <div className="relative w-full max-w-3xl bg-card border border-border rounded-xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-border/40">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-wider bg-accent/15 text-accent border border-accent/30">
                {opportunity.type.replace(/_/g, " ")}
              </span>
              <span className="font-mono text-[10px] text-muted-foreground">• ID: {opportunity.id}</span>
            </div>
            <h2 className="font-sans text-xl font-medium text-foreground">{opportunity.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-muted-foreground hover:text-foreground rounded border border-border/40 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Tabs */}
        <div className="flex border-b border-border/40 px-6 bg-secondary/20">
          <button
            onClick={() => setTab("action")}
            className={`py-3 px-4 font-mono text-xs tracking-wider border-b-2 font-medium transition-colors ${
              tab === "action"
                ? "border-accent text-accent"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            ACTION & GUARDIAN EXECUTION
          </button>
          <button
            onClick={() => setTab("simulate")}
            className={`py-3 px-4 font-mono text-xs tracking-wider border-b-2 font-medium transition-colors ${
              tab === "simulate"
                ? "border-accent text-accent"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            FINANCIAL SIMULATOR
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {tab === "simulate" ? (
            /* Simulator Tab */
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="font-mono text-xs text-muted-foreground flex justify-between">
                    <span>DISCOUNT INCENTIVE:</span>
                    <span className="text-foreground font-medium">{discountPercent}%</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="30"
                    step="1"
                    value={discountPercent}
                    onChange={(e) => setDiscountPercent(Number(e.target.value))}
                    className="w-full accent-accent"
                  />
                  <span className="font-mono text-[9px] text-muted-foreground">Guardian Cap: 15%</span>
                </div>

                <div className="space-y-2">
                  <label className="font-mono text-xs text-muted-foreground flex justify-between">
                    <span>CAMPAIGN BUDGET:</span>
                    <span className="text-foreground font-medium">₹{budget.toLocaleString("en-IN")}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="15000"
                    step="500"
                    value={budget}
                    onChange={(e) => setBudget(Number(e.target.value))}
                    className="w-full accent-accent"
                  />
                  <span className="font-mono text-[9px] text-muted-foreground">Guardian Limit: ₹10,000</span>
                </div>
              </div>

              {simulation && (
                <div className="border border-border/60 bg-secondary/30 rounded-lg p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-border/30 pb-3">
                    <span className="font-mono text-xs tracking-wider text-muted-foreground">
                      SIMULATION PROJECTION
                    </span>
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded uppercase ${
                        simulation.guardian_precheck_status === "compliant"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                          : simulation.guardian_precheck_status === "requires_guardian_override"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                          : "bg-destructive/10 text-destructive border border-destructive/30"
                      }`}
                    >
                      {simulation.guardian_precheck_status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3 bg-card/60 rounded border border-border/40">
                      <span className="block font-mono text-[9px] text-muted-foreground">EXPECTED ORDERS</span>
                      <span className="font-mono text-lg text-foreground font-semibold">
                        {simulation.expected_orders}
                      </span>
                    </div>
                    <div className="p-3 bg-card/60 rounded border border-border/40">
                      <span className="block font-mono text-[9px] text-muted-foreground">NET REVENUE</span>
                      <span className="font-mono text-lg text-emerald-400 font-semibold">
                        ₹{simulation.expected_revenue.toLocaleString("en-IN")}
                      </span>
                    </div>
                    <div className="p-3 bg-card/60 rounded border border-border/40">
                      <span className="block font-mono text-[9px] text-muted-foreground">CAMPAIGN COST</span>
                      <span className="font-mono text-lg text-muted-foreground font-semibold">
                        ₹{simulation.campaign_cost.toLocaleString("en-IN")}
                      </span>
                    </div>
                    <div className="p-3 bg-card/60 rounded border border-border/40">
                      <span className="block font-mono text-[9px] text-muted-foreground">PROJECTED ROI</span>
                      <span className="font-mono text-lg text-accent font-semibold">
                        {simulation.breakdown.roi_percentage}%
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-muted-foreground font-mono leading-relaxed pt-2">
                    {simulation.recommendation}
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Action & Guardian Tab */
            <div className="space-y-6">
              {/* Rationale Box */}
              <div className="p-4 bg-secondary/30 rounded-lg border border-border/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] tracking-wider text-muted-foreground">
                    ANALYTICAL RATIONALE
                  </span>
                  <span className="font-mono text-[10px] text-accent">
                    {opportunity.reasoning_source === "llm" ? "OpenAI LLM Reasoner" : "Deterministic Engine"}
                  </span>
                </div>
                <p className="text-xs text-foreground leading-relaxed">
                  {opportunity.reasoning || opportunity.reason}
                </p>
              </div>

              {/* Step 1: Preview Action with Guardian */}
              {!preview ? (
                <div className="p-6 border border-border/60 rounded-lg text-center space-y-3 bg-card/30">
                  <Shield className="h-8 w-8 text-accent mx-auto" />
                  <h4 className="font-mono text-sm text-foreground">PROPOSE ACTION & RUN GUARDIAN POLICY CHECK</h4>
                  <p className="text-xs text-muted-foreground max-w-md mx-auto">
                    Strategist agent will construct execution payload and submit to Guardian for financial safety verification.
                  </p>
                  <button
                    onClick={() => previewMutation.mutate()}
                    disabled={previewMutation.isPending}
                    className="px-5 py-2.5 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity disabled:opacity-50 inline-flex items-center gap-2"
                  >
                    {previewMutation.isPending ? "GUARDIAN EVALUATING..." : "RUN GUARDIAN PREVIEW"}
                  </button>
                </div>
              ) : (
                /* Guardian Evaluation Result */
                <div className="space-y-5">
                  <div
                    className={`p-4 rounded-lg border flex items-center justify-between ${
                      preview.guardian_result.decision === "approved"
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        : preview.guardian_result.decision === "requires_approval"
                        ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                        : "bg-destructive/10 border-destructive/30 text-destructive"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {preview.guardian_result.decision === "approved" ? (
                        <CheckCircle2 className="h-5 w-5" />
                      ) : preview.guardian_result.decision === "requires_approval" ? (
                        <AlertTriangle className="h-5 w-5" />
                      ) : (
                        <XCircle className="h-5 w-5" />
                      )}
                      <div>
                        <span className="font-mono text-xs font-semibold uppercase tracking-wider block">
                          GUARDIAN DECISION: {preview.guardian_result.decision.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs opacity-90">{preview.guardian_result.reason}</span>
                      </div>
                    </div>
                  </div>

                  {/* Policy Rule Checks Breakdown */}
                  <div className="border border-border/60 rounded-lg p-4 bg-secondary/20 space-y-2">
                    <span className="font-mono text-[10px] tracking-wider text-muted-foreground block mb-2">
                      DETERMINISTIC GUARDIAN RULES VERIFICATION:
                    </span>
                    {preview.guardian_result.policy_checks.map((check, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs font-mono py-1 border-b border-border/20 last:border-0">
                        <span className="text-muted-foreground">{check.rule_name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-foreground">{check.message}</span>
                          {check.passed ? (
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <X className="h-3.5 w-3.5 text-destructive" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Execution / Approval Stage */}
                  {!execution ? (
                    <div className="pt-2 flex items-center justify-end gap-3">
                      {preview.status === "awaiting_approval" && (
                        <button
                          onClick={() => approveMutation.mutate(preview.action_id)}
                          disabled={approveMutation.isPending}
                          className="px-4 py-2 bg-amber-500 text-black font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                          {approveMutation.isPending ? "AUTHORIZING..." : "MERCHANT AUTHORIZE ACTION"}
                        </button>
                      )}

                      {preview.status === "blocked" ? (
                        <div className="text-destructive font-mono text-xs">
                          ACTION BLOCKED BY GUARDIAN POLICY
                        </div>
                      ) : (
                        <button
                          onClick={() => executeMutation.mutate(preview.action_id)}
                          disabled={
                            executeMutation.isPending ||
                            preview.status === "awaiting_approval" ||
                            preview.status === "blocked"
                          }
                          className="px-5 py-2 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
                        >
                          <Play className="h-3.5 w-3.5 fill-current" />
                          {executeMutation.isPending
                            ? "DISPATCHING TO RAZORPAY..."
                            : "DISPATCH VIA RAZORPAY ADAPTER"}
                        </button>
                      )}
                    </div>
                  ) : (
                    /* Execution Success Banner */
                    <div className="p-5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg space-y-3">
                      <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-semibold">
                        <CheckCircle2 className="h-4 w-4" /> ACTION EXECUTED VIA RAZORPAY ADAPTER
                      </div>

                      {execution.execution_result && (
                        <div className="space-y-2 text-xs font-mono">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Payment Link ID:</span>
                            <span className="text-foreground">{execution.execution_result.payment_link_id}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Reference ID:</span>
                            <span className="text-foreground">{execution.execution_result.reference_id}</span>
                          </div>
                          {execution.execution_result.short_url && (
                            <div className="flex items-center justify-between pt-2 border-t border-emerald-500/20">
                              <span className="text-muted-foreground">Checkout URL:</span>
                              <div className="flex items-center gap-2">
                                <a
                                  href={execution.execution_result.short_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-accent hover:underline flex items-center gap-1"
                                >
                                  {execution.execution_result.short_url}
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                                <button
                                  onClick={() => copyPaymentUrl(execution.execution_result!.short_url!)}
                                  className="p-1 rounded bg-secondary hover:bg-secondary/80 text-foreground"
                                  title="Copy URL"
                                >
                                  {copiedLink ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
