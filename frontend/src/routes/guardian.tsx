import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, GuardianPolicy } from "@/lib/api";
import {
  ArrowLeft,
  Shield,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Save,
  RefreshCw,
  Lock,
  Percent,
  DollarSign,
  Users,
  Cpu,
  Check,
  X,
} from "lucide-react";

export const Route = createFileRoute("/guardian")({
  head: () => ({
    meta: [
      { title: "GUARDIAN — PayPilot" },
      { name: "description", content: "Deterministic financial policy and safety gatekeeper." },
    ],
  }),
  component: GuardianView,
});

function GuardianView() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<GuardianPolicy>>({});
  const [isSaved, setIsSaved] = useState(false);

  // Sandbox Tester State
  const [testDiscount, setTestDiscount] = useState<number>(10);
  const [testBudget, setTestBudget] = useState<number>(4000);
  const [testCustomers, setTestCustomers] = useState<number>(120);
  const [testConfidence, setTestConfidence] = useState<number>(0.85);

  const { data: policy, isLoading, refetch } = useQuery({
    queryKey: ["guardian-policies"],
    queryFn: () => api.getGuardianPolicies(),
  });

  useEffect(() => {
    if (policy) {
      setFormData({
        max_discount_percent: policy.max_discount_percent,
        max_campaign_budget: policy.max_campaign_budget,
        max_customer_count: policy.max_customer_count,
        min_ai_confidence: policy.min_ai_confidence,
        require_approval_above_amount: policy.require_approval_above_amount,
      });
    }
  }, [policy]);

  const updateMutation = useMutation({
    mutationFn: (updated: Partial<GuardianPolicy>) => api.updateGuardianPolicies(updated),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["guardian-policies"] });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    },
  });

  // Sandbox calculation
  const maxDiscount = formData.max_discount_percent ?? 15;
  const maxBudget = formData.max_campaign_budget ?? 10000;
  const maxCustomers = formData.max_customer_count ?? 500;
  const minConfidence = formData.min_ai_confidence ?? 0.75;
  const approvalLimit = formData.require_approval_above_amount ?? 5000;

  const discountPassed = testDiscount <= maxDiscount;
  const budgetPassed = testBudget <= maxBudget;
  const customersPassed = testCustomers <= maxCustomers;
  const confidencePassed = testConfidence >= minConfidence;
  const requiresApproval = testBudget > approvalLimit;

  let sandboxDecision = "approved";
  let sandboxReason = "Compliant with all merchant financial policies.";

  if (!discountPassed) {
    sandboxDecision = "blocked";
    sandboxReason = `Discount ${testDiscount}% exceeds maximum policy cap (${maxDiscount}%).`;
  } else if (!budgetPassed) {
    sandboxDecision = "blocked";
    sandboxReason = `Campaign budget ₹${testBudget} exceeds maximum cap (₹${maxBudget}).`;
  } else if (!customersPassed) {
    sandboxDecision = "blocked";
    sandboxReason = `Cohort size ${testCustomers} exceeds maximum limit (${maxCustomers}).`;
  } else if (!confidencePassed) {
    sandboxDecision = "blocked";
    sandboxReason = `AI Confidence ${(testConfidence * 100).toFixed(0)}% is below threshold (${(minConfidence * 100).toFixed(0)}%).`;
  } else if (requiresApproval) {
    sandboxDecision = "requires_approval";
    sandboxReason = `Exposure ₹${testBudget} exceeds autonomous threshold (₹${approvalLimit}). Merchant sign-off mandatory.`;
  }

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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">GUARDIAN</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded font-mono text-[10px] text-emerald-400">
            <Shield className="h-3.5 w-3.5" />
            <span>POLICY ENGINE ENFORCED</span>
          </div>
        </div>

        {/* Header */}
        <div className="mb-8">
          <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
            DETERMINISTIC FINANCIAL BOUNDARIES
          </div>
          <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
            Guardian Safety Center
          </h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
            Guardian is the non-negotiable policy layer. No AI recommendation can execute or disburse funds without satisfying every merchant-defined boundary.
          </p>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              FETCHING GUARDIAN POLICY LEDGER...
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Policy Configuration Form */}
            <div className="lg:col-span-7 space-y-6">
              <div className="border border-border/60 bg-card/40 rounded-xl p-6 backdrop-blur-sm space-y-6">
                <div className="flex items-center justify-between border-b border-border/40 pb-4">
                  <div>
                    <h3 className="font-mono text-sm tracking-wider text-foreground">
                      MERCHANT POLICY THRESHOLDS
                    </h3>
                    <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
                      Deterministic constraints applied to all Scout & Strategist actions
                    </p>
                  </div>
                  {isSaved && (
                    <span className="flex items-center gap-1 font-mono text-xs text-emerald-400">
                      <CheckCircle2 className="h-3.5 w-3.5" /> SAVED
                    </span>
                  )}
                </div>

                <div className="space-y-5">
                  {/* Rule 1: Max Discount */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Percent className="h-3.5 w-3.5 text-accent" /> MAXIMUM DISCOUNT PERCENTAGE
                      </span>
                      <span className="font-semibold text-accent">{formData.max_discount_percent}%</span>
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      step="1"
                      value={formData.max_discount_percent ?? 15}
                      onChange={(e) =>
                        setFormData({ ...formData, max_discount_percent: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                    <span className="font-mono text-[9px] text-muted-foreground block">
                      Actions exceeding this rate will be immediately BLOCKED by Guardian.
                    </span>
                  </div>

                  {/* Rule 2: Max Campaign Budget */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <DollarSign className="h-3.5 w-3.5 text-accent" /> MAXIMUM CAMPAIGN BUDGET
                      </span>
                      <span className="font-semibold text-foreground">
                        ₹{(formData.max_campaign_budget ?? 10000).toLocaleString("en-IN")}
                      </span>
                    </label>
                    <input
                      type="range"
                      min="2000"
                      max="30000"
                      step="1000"
                      value={formData.max_campaign_budget ?? 10000}
                      onChange={(e) =>
                        setFormData({ ...formData, max_campaign_budget: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                  </div>

                  {/* Rule 3: Max Customer Cohort Count */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Users className="h-3.5 w-3.5 text-accent" /> MAXIMUM CUSTOMER COHORT
                      </span>
                      <span className="font-semibold text-foreground">
                        {formData.max_customer_count} accounts
                      </span>
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="1000"
                      step="25"
                      value={formData.max_customer_count ?? 500}
                      onChange={(e) =>
                        setFormData({ ...formData, max_customer_count: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                  </div>

                  {/* Rule 4: Min AI Confidence */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Cpu className="h-3.5 w-3.5 text-accent" /> MINIMUM AI CONFIDENCE THRESHOLD
                      </span>
                      <span className="font-semibold text-foreground">
                        {((formData.min_ai_confidence ?? 0.75) * 100).toFixed(0)}%
                      </span>
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="0.95"
                      step="0.05"
                      value={formData.min_ai_confidence ?? 0.75}
                      onChange={(e) =>
                        setFormData({ ...formData, min_ai_confidence: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                  </div>

                  {/* Rule 5: Approval Required Above Amount */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Lock className="h-3.5 w-3.5 text-amber-400" /> AUTONOMOUS EXECUTION CAP
                      </span>
                      <span className="font-semibold text-amber-400">
                        ₹{(formData.require_approval_above_amount ?? 5000).toLocaleString("en-IN")}
                      </span>
                    </label>
                    <input
                      type="range"
                      min="1000"
                      max="20000"
                      step="500"
                      value={formData.require_approval_above_amount ?? 5000}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          require_approval_above_amount: Number(e.target.value),
                        })
                      }
                      className="w-full accent-amber-500"
                    />
                    <span className="font-mono text-[9px] text-muted-foreground block">
                      Campaigns exceeding this budget require explicit merchant sign-off before execution.
                    </span>
                  </div>
                </div>

                <div className="pt-4 border-t border-border/40 flex justify-end">
                  <button
                    onClick={() => updateMutation.mutate(formData)}
                    disabled={updateMutation.isPending}
                    className="px-6 py-2.5 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                  >
                    <Save className="h-3.5 w-3.5" />
                    {updateMutation.isPending ? "SAVING POLICY..." : "COMMIT POLICY UPDATES"}
                  </button>
                </div>
              </div>
            </div>

            {/* Guardian Sandbox & Live Policy Verifier */}
            <div className="lg:col-span-5 space-y-6">
              <div className="border border-border/60 bg-secondary/20 rounded-xl p-6 backdrop-blur-sm space-y-5">
                <div className="flex items-center justify-between border-b border-border/40 pb-3">
                  <span className="font-mono text-xs tracking-wider text-foreground">
                    GUARDIAN SANDBOX VERIFIER
                  </span>
                  <span className="font-mono text-[9px] text-accent">REAL-TIME SIMULATION</span>
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed">
                  Test hypothetical action payloads against your live Guardian boundaries to preview enforcement results.
                </p>

                {/* Sandbox Inputs */}
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="p-3 bg-card/60 rounded border border-border/40">
                    <span className="text-[9px] text-muted-foreground block">TEST DISCOUNT</span>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-foreground font-semibold">{testDiscount}%</span>
                      <div className="flex gap-1">
                        <button
                          onClick={() => setTestDiscount((d) => Math.max(0, d - 5))}
                          className="px-1.5 bg-secondary rounded hover:bg-secondary/80"
                        >
                          -
                        </button>
                        <button
                          onClick={() => setTestDiscount((d) => d + 5)}
                          className="px-1.5 bg-secondary rounded hover:bg-secondary/80"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-card/60 rounded border border-border/40">
                    <span className="text-[9px] text-muted-foreground block">TEST BUDGET</span>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-foreground font-semibold">₹{testBudget}</span>
                      <div className="flex gap-1">
                        <button
                          onClick={() => setTestBudget((b) => Math.max(500, b - 1000))}
                          className="px-1.5 bg-secondary rounded hover:bg-secondary/80"
                        >
                          -
                        </button>
                        <button
                          onClick={() => setTestBudget((b) => b + 1000)}
                          className="px-1.5 bg-secondary rounded hover:bg-secondary/80"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Live Decision Card */}
                <div
                  className={`p-4 rounded-lg border space-y-2 ${
                    sandboxDecision === "approved"
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : sandboxDecision === "requires_approval"
                      ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                      : "bg-destructive/10 border-destructive/30 text-destructive"
                  }`}
                >
                  <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase">
                    {sandboxDecision === "approved" ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : sandboxDecision === "requires_approval" ? (
                      <AlertTriangle className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    <span>DECISION: {sandboxDecision.replace(/_/g, " ")}</span>
                  </div>
                  <p className="text-xs opacity-90 leading-relaxed font-sans">{sandboxReason}</p>
                </div>

                {/* Checklist */}
                <div className="space-y-1.5 pt-2 border-t border-border/30 font-mono text-xs">
                  <div className="flex justify-between py-1 border-b border-border/20">
                    <span className="text-muted-foreground">Discount Rate ({testDiscount}% vs ≤{maxDiscount}%):</span>
                    {discountPassed ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        PASS <Check className="h-3 w-3" />
                      </span>
                    ) : (
                      <span className="text-destructive flex items-center gap-1">
                        FAIL <X className="h-3 w-3" />
                      </span>
                    )}
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/20">
                    <span className="text-muted-foreground">Budget Cap (₹{testBudget} vs ≤₹{maxBudget}):</span>
                    {budgetPassed ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        PASS <Check className="h-3 w-3" />
                      </span>
                    ) : (
                      <span className="text-destructive flex items-center gap-1">
                        FAIL <X className="h-3 w-3" />
                      </span>
                    )}
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-muted-foreground">Auto-Execute (₹{testBudget} vs ≤₹{approvalLimit}):</span>
                    {!requiresApproval ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        AUTONOMOUS <Check className="h-3 w-3" />
                      </span>
                    ) : (
                      <span className="text-amber-400 flex items-center gap-1">
                        SIGN-OFF REQUIRED <AlertTriangle className="h-3 w-3" />
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
