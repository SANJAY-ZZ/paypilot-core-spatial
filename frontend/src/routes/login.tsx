import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { auth } from "@/lib/auth";
import {
  Shield,
  ArrowRight,
  Sparkles,
  Lock,
  Mail,
  CheckCircle2,
  Building2,
} from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "LOGIN — PayPilot AI Revenue OS" },
      { name: "description", content: "Merchant access to the PayPilot AI Revenue Operating System." },
    ],
  }),
  component: LoginView,
});

function LoginView() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("arjun@koraretail.com");
  const [password, setPassword] = useState("••••••••••••");
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      auth.login(email, password);
      setIsLoading(false);
      navigate({ to: "/" });
    }, 600);
  };

  const handleDemoSignIn = () => {
    setIsLoading(true);
    setTimeout(() => {
      auth.loginAsDemo();
      setIsLoading(false);
      navigate({ to: "/" });
    }, 400);
  };

  return (
    <div className="min-h-screen w-full bg-background text-foreground flex items-center justify-center p-6 relative overflow-hidden">
      {/* Cinematic Ambient Glow Background */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(226,89,58,0.12)_0%,transparent_60%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(226,89,58,0.06)_0%,transparent_50%)]" />

      {/* Decorative Grid Lines */}
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#8b8f9608_1px,transparent_1px),linear-gradient(to_bottom,#8b8f9608_1px,transparent_1px)] bg-[size:4rem_4rem]" />

      <div className="relative w-full max-w-md bg-card/60 border border-border/70 rounded-2xl shadow-2xl backdrop-blur-2xl p-8 space-y-8 animate-fade-in">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
            </span>
            <span className="font-mono text-[10px] tracking-[0.4em] text-accent uppercase font-medium">
              DEMO ENVIRONMENT
            </span>
          </div>

          <h1 className="font-mono text-2xl tracking-[0.35em] text-foreground font-bold">
            PAYPILOT
          </h1>
          <p className="font-mono text-[10px] tracking-[0.25em] text-muted-foreground uppercase">
            AI Revenue Operating System
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSignIn} className="space-y-4">
          <div className="space-y-1.5">
            <label className="font-mono text-[10px] tracking-wider text-muted-foreground uppercase flex items-center gap-1.5">
              <Mail className="h-3 w-3 text-accent" /> Merchant Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-secondary/40 border border-border/60 rounded-lg text-xs font-mono text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <div className="space-y-1.5">
            <label className="font-mono text-[10px] tracking-wider text-muted-foreground uppercase flex items-center gap-1.5">
              <Lock className="h-3 w-3 text-accent" /> Access Token / Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-secondary/40 border border-border/60 rounded-lg text-xs font-mono text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 bg-accent hover:bg-accent/90 text-accent-foreground font-mono text-xs rounded-lg font-semibold tracking-wider transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
          >
            {isLoading ? "AUTHENTICATING..." : "SIGN IN TO REVENUE OS"}
            {!isLoading && <ArrowRight className="h-3.5 w-3.5" />}
          </button>
        </form>

        {/* Divider */}
        <div className="relative flex items-center justify-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border/50" />
          </div>
          <span className="relative px-3 bg-card font-mono text-[9px] tracking-[0.2em] text-muted-foreground uppercase">
            OR EXPLORE INSTANTLY
          </span>
        </div>

        {/* Demo Merchant Quick-Entry Button */}
        <div className="space-y-3">
          <button
            type="button"
            onClick={handleDemoSignIn}
            disabled={isLoading}
            className="w-full py-3 px-4 bg-secondary/70 hover:bg-secondary border border-border/80 hover:border-accent/50 rounded-xl text-left transition-all group flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-card border border-border/60 text-accent group-hover:border-accent/50 transition-colors">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <div className="font-mono text-xs text-foreground font-semibold flex items-center gap-1.5">
                  <span>CONTINUE AS KORA RETAIL</span>
                  <span className="text-[8px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                    DEMO MERCHANT
                  </span>
                </div>
                <div className="font-mono text-[10px] text-muted-foreground">
                  ₹8.42L Revenue • 1,024 Verified Customers
                </div>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-accent transition-transform group-hover:translate-x-0.5" />
          </button>
        </div>

        {/* Security & Prototype Notice */}
        <div className="pt-2 border-t border-border/30 text-center font-mono text-[9px] text-muted-foreground/70 leading-relaxed">
          <span>Protected by PayPilot Guardian Deterministic Gatekeeper • Buildathon Sandbox</span>
        </div>
      </div>
    </div>
  );
}
