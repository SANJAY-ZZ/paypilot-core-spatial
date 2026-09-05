import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, GuardianPolicy } from "@/lib/api";
import { auth, MerchantContext } from "@/lib/auth";
import {
  ArrowLeft,
  Settings,
  Shield,
  Building2,
  Cpu,
  Database,
  CheckCircle2,
  AlertTriangle,
  Save,
  RefreshCw,
  Sliders,
  DollarSign,
  Users,
  Percent,
  Lock,
} from "lucide-react";

export const Route = createFileRoute("/admin")({
  head: () => ({
    meta: [
      { title: "ADMIN — PayPilot" },
      { name: "description", content: "Merchant & System Configuration Center." },
    ],
  }),
  component: AdminView,
});

function AdminView() {
  const queryClient = useQueryClient();
  const [activeMerchant, setActiveMerchant] = useState<MerchantContext>(auth.getActiveMerchant());
  const [guardianForm, setGuardianForm] = useState<Partial<GuardianPolicy>>({});
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    return auth.subscribe(() => setActiveMerchant(auth.getActiveMerchant()));
  }, []);

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.getHealth(),
  });

  const { data: policy, isLoading: isPolicyLoading } = useQuery({
    queryKey: ["guardian-policies"],
    queryFn: () => api.getGuardianPolicies(),
  });

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });

  useEffect(() => {
    if (policy) {
      setGuardianForm({
        max_discount_percent: policy.max_discount_percent,
        max_campaign_budget: policy.max_campaign_budget,
        max_customer_count: policy.max_customer_count,
        min_ai_confidence: policy.min_ai_confidence,
        require_approval_above_amount: policy.require_approval_above_amount,
      });
    }
  }, [policy]);

  const updatePolicyMutation = useMutation({
    mutationFn: (updated: Partial<GuardianPolicy>) => api.updateGuardianPolicies(updated),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["guardian-policies"] });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    },
  });

  return (
    <ApplicationShell>
      <main className="min-h-screen pt-20 pb-16 px-8 max-w-[1600px] mx-auto space-y-8">
        {/* Breadcrumb */}
        <div className="flex items-center justify-between border-b border-border/40 pb-6">
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
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">ADMIN</span>
          </div>

          <div className="flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
            <Settings className="h-3.5 w-3.5 text-accent" />
            <span>MERCHANT CONFIGURATION & ENGINE SETTINGS</span>
          </div>
        </div>

        {/* Header */}
        <div>
          <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
            CONTROL PLANE
          </div>
          <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
            Merchant & System Administration
          </h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-2xl font-sans">
            Configure financial safety boundaries, view backend connection states, and manage merchant ecosystem parameters.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Merchant Profile & System Telemetry */}
          <div className="lg:col-span-5 space-y-6">
            {/* Merchant Profile */}
            <div className="border border-border/60 bg-card/40 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center justify-between border-b border-border/40 pb-3">
                <div className="flex items-center gap-2 font-mono text-xs text-foreground font-semibold">
                  <Building2 className="h-4 w-4 text-accent" /> MERCHANT PROFILE
                </div>
                <span className="px-2 py-0.5 rounded text-[9px] font-mono uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  {activeMerchant.status}
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Merchant Name:</span>
                  <span className="text-foreground font-medium">{activeMerchant.name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Merchant ID:</span>
                  <span className="text-foreground">{activeMerchant.id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Operating Currency:</span>
                  <span className="text-accent font-semibold">{activeMerchant.currency} (INR)</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-muted-foreground">Category:</span>
                  <span className="text-foreground">{activeMerchant.category}</span>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="border border-border/60 bg-card/40 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center justify-between border-b border-border/40 pb-3">
                <div className="flex items-center gap-2 font-mono text-xs text-foreground font-semibold">
                  <Cpu className="h-4 w-4 text-accent" /> SYSTEM & RUNTIME TELEMETRY
                </div>
                <span className="px-2 py-0.5 rounded text-[9px] font-mono uppercase bg-accent/15 text-accent border border-accent/30">
                  {health?.environment || "DEVELOPMENT"}
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Service:</span>
                  <span className="text-foreground">{health?.service || "PayPilot AI Engine"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Version:</span>
                  <span className="text-foreground">{health?.version || "v1.0.0"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Database Connected:</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> ACTIVE
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/20">
                  <span className="text-muted-foreground">Razorpay Gateway:</span>
                  <span className="text-foreground font-semibold flex items-center gap-1.5">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        health?.razorpay?.status === "connected"
                          ? "bg-emerald-400"
                          : health?.razorpay?.status === "not_configured"
                          ? "bg-muted-foreground"
                          : "bg-amber-400"
                      }`}
                    />
                    {health?.razorpay
                      ? `${health.razorpay.mode.toUpperCase()} (${health.razorpay.status.toUpperCase()})`
                      : (health?.razorpay_mode || "MOCK").toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-muted-foreground">Reasoning Engine:</span>
                  <span className="text-foreground font-semibold flex items-center gap-1.5">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        health?.llm?.status === "connected"
                          ? "bg-emerald-400"
                          : "bg-amber-400"
                      }`}
                    />
                    {health?.llm
                      ? `${health.llm.provider.toUpperCase()} (${health.llm.model})`
                      : "Ollama (gemma4:latest)"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Guardian Policy Rules Configuration */}
          <div className="lg:col-span-7 space-y-6">
            <div className="border border-border/60 bg-card/40 rounded-xl p-6 backdrop-blur-sm space-y-6">
              <div className="flex items-center justify-between border-b border-border/40 pb-4">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-accent" />
                  <div>
                    <h3 className="font-mono text-xs tracking-wider text-foreground font-semibold">
                      ACTIVE GUARDIAN FINANCIAL POLICIES
                    </h3>
                    <p className="font-mono text-[9px] text-muted-foreground">
                      Authoritative policy limits enforced before any action execution
                    </p>
                  </div>
                </div>
                {isSaved && (
                  <span className="flex items-center gap-1 font-mono text-xs text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" /> SAVED
                  </span>
                )}
              </div>

              {isPolicyLoading ? (
                <div className="py-12 text-center text-muted-foreground font-mono text-xs">
                  Loading Guardian policies...
                </div>
              ) : (
                <div className="space-y-5">
                  {/* Max Discount */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Percent className="h-3.5 w-3.5 text-accent" /> MAX DISCOUNT PERCENTAGE
                      </span>
                      <span className="font-semibold text-accent">{guardianForm.max_discount_percent}%</span>
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      step="1"
                      value={guardianForm.max_discount_percent ?? 15}
                      onChange={(e) =>
                        setGuardianForm({ ...guardianForm, max_discount_percent: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                  </div>

                  {/* Max Budget */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <DollarSign className="h-3.5 w-3.5 text-accent" /> MAX CAMPAIGN BUDGET
                      </span>
                      <span className="font-semibold text-foreground">
                        ₹{(guardianForm.max_campaign_budget ?? 10000).toLocaleString("en-IN")}
                      </span>
                    </label>
                    <input
                      type="range"
                      min="2000"
                      max="30000"
                      step="1000"
                      value={guardianForm.max_campaign_budget ?? 10000}
                      onChange={(e) =>
                        setGuardianForm({ ...guardianForm, max_campaign_budget: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                  </div>

                  {/* Max Cohort */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Users className="h-3.5 w-3.5 text-accent" /> MAX COHORT SIZE
                      </span>
                      <span className="font-semibold text-foreground">
                        {guardianForm.max_customer_count} accounts
                      </span>
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="1000"
                      step="25"
                      value={guardianForm.max_customer_count ?? 500}
                      onChange={(e) =>
                        setGuardianForm({ ...guardianForm, max_customer_count: Number(e.target.value) })
                      }
                      className="w-full accent-accent"
                    />
                  </div>

                  {/* Autonomous Limit */}
                  <div className="space-y-2">
                    <label className="font-mono text-xs text-muted-foreground flex justify-between">
                      <span className="flex items-center gap-1.5 text-foreground">
                        <Lock className="h-3.5 w-3.5 text-amber-400" /> AUTONOMOUS EXECUTION THRESHOLD
                      </span>
                      <span className="font-semibold text-amber-400">
                        ₹{(guardianForm.require_approval_above_amount ?? 5000).toLocaleString("en-IN")}
                      </span>
                    </label>
                    <input
                      type="range"
                      min="1000"
                      max="20000"
                      step="500"
                      value={guardianForm.require_approval_above_amount ?? 5000}
                      onChange={(e) =>
                        setGuardianForm({
                          ...guardianForm,
                          require_approval_above_amount: Number(e.target.value),
                        })
                      }
                      className="w-full accent-amber-500"
                    />
                  </div>

                  <div className="pt-4 border-t border-border/40 flex justify-end">
                    <button
                      onClick={() => updatePolicyMutation.mutate(guardianForm)}
                      disabled={updatePolicyMutation.isPending}
                      className="px-6 py-2.5 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                    >
                      <Save className="h-3.5 w-3.5" />
                      {updatePolicyMutation.isPending ? "SAVING..." : "COMMIT POLICY UPDATES"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </ApplicationShell>
  );
}
