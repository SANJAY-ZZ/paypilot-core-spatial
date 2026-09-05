import { useEffect, useState, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { coreState } from "@/lib/core-state";
import {
  Search,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Users,
  Shield,
  Zap,
  FileText,
  ShoppingBag,
  Bot,
  Settings,
  RefreshCw,
  LogOut,
  Compass,
  X,
  CornerDownLeft,
} from "lucide-react";

interface CommandItem {
  id: string;
  title: string;
  description: string;
  category: "Navigation" | "Agent Actions" | "System";
  icon: React.ReactNode;
  action: () => void;
  shortcut?: string;
}

export function CommandPalette({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const scanMutation = useMutation({
    mutationFn: () => api.scanOpportunities(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      onClose();
      navigate({ to: "/opportunities" });
    },
  });

  const commands: CommandItem[] = [
    {
      id: "core",
      title: "Return to PayPilot Core",
      description: "Navigate to the living 3D spatial intelligence Core",
      category: "Navigation",
      icon: <Compass className="h-4 w-4 text-accent" />,
      action: () => {
        onClose();
        navigate({ to: "/", search: { state: "active" } });
      },
      shortcut: "G C",
    },
    {
      id: "revenue",
      title: "Revenue Command",
      description: "Gross revenue overview, pool metrics, and telemetry",
      category: "Navigation",
      icon: <TrendingUp className="h-4 w-4 text-emerald-400" />,
      action: () => {
        onClose();
        navigate({ to: "/dashboard" });
      },
      shortcut: "G R",
    },
    {
      id: "opportunities",
      title: "Revenue Opportunities",
      description: "Scout candidate queue with LLM reasoning synthesis",
      category: "Navigation",
      icon: <Sparkles className="h-4 w-4 text-amber-400" />,
      action: () => {
        onClose();
        navigate({ to: "/opportunities" });
      },
      shortcut: "G O",
    },
    {
      id: "copilot",
      title: "AI Revenue Copilot",
      description: "Operational high-impact AI strategy and 1-click execution",
      category: "Navigation",
      icon: <Bot className="h-4 w-4 text-accent" />,
      action: () => {
        onClose();
        navigate({ to: "/copilot" });
      },
      shortcut: "G A",
    },
    {
      id: "customers",
      title: "Customer Intelligence",
      description: "Customer cohorts, churn risk matrix, and verified accounts",
      category: "Navigation",
      icon: <Users className="h-4 w-4 text-blue-400" />,
      action: () => {
        onClose();
        navigate({ to: "/customers" });
      },
      shortcut: "G U",
    },
    {
      id: "guardian",
      title: "Guardian Safety Center",
      description: "Deterministic financial boundaries and live policy sandbox",
      category: "Navigation",
      icon: <Shield className="h-4 w-4 text-emerald-400" />,
      action: () => {
        onClose();
        navigate({ to: "/guardian" });
      },
      shortcut: "G G",
    },
    {
      id: "actions",
      title: "Execution Control Center",
      description: "Autonomous action runtime stream and Razorpay link dispatch",
      category: "Navigation",
      icon: <Zap className="h-4 w-4 text-amber-400" />,
      action: () => {
        onClose();
        navigate({ to: "/actions" });
      },
      shortcut: "G E",
    },
    {
      id: "audit",
      title: "Immutable Audit Trail",
      description: "Chronological multi-agent compliance ledger & metadata",
      category: "Navigation",
      icon: <FileText className="h-4 w-4 text-purple-400" />,
      action: () => {
        onClose();
        navigate({ to: "/audit" });
      },
      shortcut: "G L",
    },
    {
      id: "commerce",
      title: "Agentic Commerce Readiness",
      description: "Autonomous buyer compatibility score and catalog health",
      category: "Navigation",
      icon: <ShoppingBag className="h-4 w-4 text-pink-400" />,
      action: () => {
        onClose();
        navigate({ to: "/commerce" });
      },
      shortcut: "G M",
    },
    {
      id: "admin",
      title: "Merchant & System Admin",
      description: "Configure policies, merchant profile, and system status",
      category: "Navigation",
      icon: <Settings className="h-4 w-4 text-muted-foreground" />,
      action: () => {
        onClose();
        navigate({ to: "/admin" });
      },
      shortcut: "G S",
    },
    {
      id: "scan",
      title: "Trigger Scout Scan",
      description: "Dispatch Scout Agent to discover fresh uncaptured revenue",
      category: "Agent Actions",
      icon: <RefreshCw className="h-4 w-4 text-accent animate-spin-hover" />,
      action: () => scanMutation.mutate(),
    },
    {
      id: "replay-intro",
      title: "Replay 3D Core Activation",
      description: "Re-run the cinematic intro scroll sequence",
      category: "System",
      icon: <Compass className="h-4 w-4 text-muted-foreground" />,
      action: () => {
        coreState.resetToIntro();
        onClose();
        navigate({ to: "/", search: { state: "intro" } });
      },
    },
    {
      id: "sign-out",
      title: "Sign Out",
      description: "Exit demo merchant session and return to login screen",
      category: "System",
      icon: <LogOut className="h-4 w-4 text-destructive" />,
      action: () => {
        auth.logout();
        onClose();
        navigate({ to: "/login" });
      },
    },
  ];

  const filtered = commands.filter((c) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      c.title.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      c.category.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open
        }
      } else if (e.key === "Escape" && isOpen) {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      e.preventDefault();
      filtered[selectedIndex].action();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-background/80 backdrop-blur-md animate-fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-card border border-border/80 rounded-xl shadow-2xl overflow-hidden backdrop-blur-xl flex flex-col max-h-[75vh]"
      >
        {/* Search Bar */}
        <div className="flex items-center px-4 border-b border-border/60 py-3.5 gap-3">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or jump to module..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-sm font-mono text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
          />
          <div className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground/80 bg-secondary/80 px-2 py-0.5 rounded border border-border/40">
            <span>ESC</span>
          </div>
        </div>

        {/* Command List */}
        <div className="overflow-y-auto p-2 space-y-1 flex-1">
          {filtered.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground font-mono text-xs">
              No matching commands or routes.
            </div>
          ) : (
            filtered.map((item, index) => (
              <button
                key={item.id}
                onClick={item.action}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-left transition-all ${
                  selectedIndex === index
                    ? "bg-accent/15 border border-accent/40 text-foreground"
                    : "text-muted-foreground hover:bg-secondary/40 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded bg-secondary/80 border border-border/50">
                    {item.icon}
                  </div>
                  <div>
                    <div className="font-mono text-xs text-foreground font-medium flex items-center gap-2">
                      <span>{item.title}</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground font-normal">
                        {item.category}
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground/80 font-sans mt-0.5 line-clamp-1">
                      {item.description}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {item.shortcut && (
                    <span className="font-mono text-[9px] text-muted-foreground/70 bg-secondary/50 px-1.5 py-0.5 rounded border border-border/30">
                      {item.shortcut}
                    </span>
                  )}
                  {selectedIndex === index && (
                    <CornerDownLeft className="h-3.5 w-3.5 text-accent" />
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-border/40 bg-secondary/20 flex items-center justify-between font-mono text-[10px] text-muted-foreground">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Dismiss</span>
          </div>
          <span className="text-accent font-medium">PAYPILOT COMMAND</span>
        </div>
      </div>
    </div>
  );
}
