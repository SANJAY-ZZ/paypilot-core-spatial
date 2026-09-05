import { ReactNode, useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Command, Activity, Shield } from "lucide-react";
import { api } from "@/lib/api";
import { CommandPalette } from "./CommandPalette";
import { ActivityPanel } from "./ActivityPanel";
import { MerchantMenu } from "./MerchantMenu";

export function ApplicationShell({ children }: { children: ReactNode }) {
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isActivityOpen, setIsActivityOpen] = useState(false);

  // System Health Telemetry
  const { data: health, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.getHealth(),
    refetchInterval: 15000,
  });

  // Global Command Palette Shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      {/* Header Chrome */}
      <header className="fixed inset-x-0 top-0 z-40 h-14 bg-background/70 backdrop-blur-md">
        <div className="mx-auto flex h-full max-w-[1600px] items-center justify-between px-8">
          {/* Logo & Health Status */}
          <div className="flex items-center gap-4">
            <Link
              to="/"
              search={{ state: "active" }}
              className="font-mono text-[13px] tracking-[0.42em] text-foreground transition-opacity hover:opacity-70"
            >
              PAYPILOT
            </Link>

            <div className="hidden sm:flex items-center gap-1.5 pl-3 border-l border-border/50">
              <span className="relative flex h-2 w-2">
                {health?.status === "healthy" ? (
                  <>
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  </>
                ) : isError ? (
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-destructive" />
                ) : (
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                )}
              </span>
              <span className="font-mono text-[9px] tracking-[0.2em] text-muted-foreground">
                {health?.status === "healthy" ? "ONLINE" : isError ? "OFFLINE" : "CONNECTING"}
              </span>
            </div>
          </div>

          {/* Central Spatial Anchor */}
          <div className="pointer-events-none absolute left-1/2 -translate-x-1/2">
            <Link
              to="/"
              search={{ state: "active" }}
              className="pointer-events-auto font-mono text-[10px] tracking-[0.5em] text-muted-foreground hover:text-foreground transition-colors"
            >
              CORE
            </Link>
          </div>

          {/* Navigation Controls */}
          <nav className="flex items-center gap-6">
            {/* Command Palette Trigger */}
            <button
              onClick={() => setIsCommandOpen(true)}
              className="flex items-center gap-2 font-mono text-[10px] tracking-[0.28em] text-muted-foreground transition-colors hover:text-foreground"
              title="Command Palette (Cmd/Ctrl + K)"
            >
              <Command className="h-3 w-3" strokeWidth={1.5} />
              <span className="hidden md:inline">COMMAND</span>
              <span className="hidden lg:inline-block font-mono text-[8px] text-muted-foreground/60 border border-border/50 px-1 py-0.2 rounded">
                ⌘K
              </span>
            </button>

            {/* Activity Drawer Trigger */}
            <button
              onClick={() => setIsActivityOpen(true)}
              className="flex items-center gap-2 font-mono text-[10px] tracking-[0.28em] text-muted-foreground transition-colors hover:text-foreground"
              title="Real-time Multi-Agent Activity"
            >
              <Activity className="h-3 w-3" strokeWidth={1.5} />
              <span className="hidden md:inline">ACTIVITY</span>
            </button>

            {/* Merchant & User Switcher Menu */}
            <MerchantMenu />
          </nav>
        </div>
        <div className="mx-8 h-px bg-border/50" />
      </header>

      {/* Main Content */}
      {children}

      {/* Command Palette Modal */}
      <CommandPalette isOpen={isCommandOpen} onClose={() => setIsCommandOpen(false)} />

      {/* Activity Panel Drawer */}
      <ActivityPanel isOpen={isActivityOpen} onClose={() => setIsActivityOpen(false)} />
    </div>
  );
}
