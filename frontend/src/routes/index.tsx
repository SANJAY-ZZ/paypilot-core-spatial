import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { HERO } from "@/data/paypilot";
import { coreProgress } from "@/lib/core-progress";
import { coreState, CoreSemanticState } from "@/lib/core-state";
import { api } from "@/lib/api";
import { ChevronDown } from "lucide-react";

const CoreScene = lazy(() => import("@/components/core/CoreScene"));

export const Route = createFileRoute("/")({
  validateSearch: (search: Record<string, unknown>) => {
    return {
      state: (search.state as "intro" | "active" | "nodes") || undefined,
    };
  },
  head: () => ({
    meta: [
      { title: "PayPilot Core — Spatial AI Revenue Operating System" },
      {
        name: "description",
        content:
          "PayPilot continuously discovers and evaluates revenue opportunities across your merchant ecosystem. Enter the spatial Core.",
      },
      { property: "og:title", content: "PayPilot Core — Spatial AI Revenue OS" },
      {
        property: "og:description",
        content:
          "A living financial system: navigate revenue, customers, opportunities and guardrails from a spatial 3D Core.",
      },
    ],
  }),
  component: Index,
});

const STAGES = [
  "CORE INITIALISING",
  "CORE ACTIVATING",
  "CORE ACTIVE",
  "DATA PATHWAYS",
  "SPATIAL NODES",
];

function Index() {
  const { state: requestedState } = Route.useSearch();
  const [mounted, setMounted] = useState(false);

  // Initialize semantic state from route param or session memory
  const initialSemantic = coreState.getInitialState(requestedState);
  const [semanticState, setSemanticState] = useState<CoreSemanticState>(initialSemantic);
  const [stage, setStage] = useState(
    initialSemantic === "INTRO" ? 0 : initialSemantic === "ACTIVE" ? 2 : 4
  );

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });

  const indicators = [
    { label: "AI CONFIDENCE", value: "94%" },
    {
      label: "OPPORTUNITIES",
      value: dashboard ? String(dashboard.opportunity_count) : "27",
    },
    {
      label: "RECOVERABLE",
      value: dashboard ? `₹${dashboard.recoverable_revenue.toLocaleString("en-IN")}` : "₹38,400",
    },
  ];

  useEffect(() => {
    setMounted(true);
  }, []);

  // Initialize progress and maintain smooth RAF loop
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    coreProgress.reducedMotion = reduced;

    const initialP = reduced
      ? 1.0
      : coreState.getProgressForState(initialSemantic);

    coreProgress.setProgressImmediate(initialP);

    let rafId = 0;
    const tick = () => {
      const diff = coreProgress.target - coreProgress.eased;
      if (Math.abs(diff) > 0.0002) {
        coreProgress.eased += diff * 0.09;
        coreProgress.value = coreProgress.eased;
      } else {
        coreProgress.eased = coreProgress.target;
        coreProgress.value = coreProgress.target;
      }

      const p = coreProgress.eased;
      const s = Math.min(4, Math.floor(p * 5));
      setStage((prev) => (prev === s ? prev : s));

      const currentSemantic = coreState.getStateFromProgress(p);
      setSemanticState((prev) => {
        if (prev !== currentSemantic) {
          coreState.setState(currentSemantic);
          return currentSemantic;
        }
        return prev;
      });

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);

    // Reliable input event listeners across mice, trackpads, touchscreens and keyboards
    const handleWheel = (e: WheelEvent) => {
      // Normalize wheel delta across varying hardware
      const delta = Math.sign(e.deltaY) * Math.min(0.09, Math.max(0.02, Math.abs(e.deltaY) * 0.0008));
      coreProgress.addDelta(delta);
    };

    let touchStartY = 0;
    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        touchStartY = e.touches[0].clientY;
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        const currentY = e.touches[0].clientY;
        const deltaY = touchStartY - currentY;
        touchStartY = currentY;
        coreProgress.addDelta(deltaY * 0.002);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "PageDown" || e.key === " ") {
        coreProgress.addDelta(0.1);
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        coreProgress.addDelta(-0.1);
      }
    };

    window.addEventListener("wheel", handleWheel, { passive: true });
    window.addEventListener("touchstart", handleTouchStart, { passive: true });
    window.addEventListener("touchmove", handleTouchMove, { passive: true });
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("wheel", handleWheel);
      window.removeEventListener("touchstart", handleTouchStart);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [requestedState, initialSemantic]);

  // Smooth hero text fadeout as user scrolls past INTRO
  const heroFade = semanticState === "INTRO" ? 1 : 0;

  return (
    <ApplicationShell>
      {/* Fixed 3D cinematic canvas */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-background" />
        {mounted && (
          <Suspense fallback={null}>
            <CoreScene />
          </Suspense>
        )}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,transparent_35%,rgba(6,6,8,0.75)_100%)]" />
      </div>

      {/* Spatial overlay typography */}
      <div className="pointer-events-none fixed inset-0 z-20">
        <div className="mx-auto flex h-full max-w-[1600px] flex-col justify-between px-10 pb-10 pt-24">
          <div
            className="max-w-xl transition-all duration-700"
            style={{ opacity: heroFade, transform: `translateY(${heroFade ? 0 : -20}px)` }}
          >
            <div className="mb-6 flex items-center gap-3">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-70" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
              </span>
              <span className="font-mono text-[10px] tracking-[0.34em] text-muted-foreground">
                {HERO.status}
              </span>
            </div>
            <h1 className="font-display text-[64px] leading-[0.95] tracking-[-0.03em] text-foreground">
              {HERO.titleLines[0]}
              <br />
              <span className="text-muted-foreground">{HERO.titleLines[1]}</span>
            </h1>
            <p className="mt-6 max-w-md text-sm leading-relaxed text-muted-foreground font-sans">
              {HERO.supporting}
            </p>
          </div>

          <div className="flex items-end justify-between">
            <div className="flex items-center gap-3">
              <span className="font-mono text-[9px] tracking-[0.32em] text-muted-foreground">
                {String(stage + 1).padStart(2, "0")} / 05
              </span>
              <span className="h-px w-16 bg-border" />
              <span className="font-mono text-[9px] tracking-[0.32em] text-accent">
                {STAGES[stage]}
              </span>
            </div>

            <div className="flex items-end gap-12">
              {indicators.map((ind) => (
                <div key={ind.label} className="text-right">
                  <div className="font-mono text-[9px] tracking-[0.3em] text-muted-foreground">
                    {ind.label}
                  </div>
                  <div className="mt-1 font-mono text-lg tracking-tight text-foreground">
                    {ind.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Semantic bottom state indicator & instructions */}
      <div className="pointer-events-none fixed bottom-5 left-1/2 z-30 -translate-x-1/2">
        {semanticState === "INTRO" ? (
          <div className="flex flex-col items-center gap-1.5 animate-bounce">
            <ChevronDown className="h-4 w-4 text-accent" />
            <span className="font-mono text-[9px] tracking-[0.35em] text-accent font-medium uppercase">
              SCROLL TO ACTIVATE CORE
            </span>
          </div>
        ) : semanticState === "ACTIVE" ? (
          <div className="flex flex-col items-center gap-1 animate-pulse">
            <ChevronDown className="h-3.5 w-3.5 text-accent/80" />
            <span className="font-mono text-[9px] tracking-[0.32em] text-muted-foreground uppercase">
              SCROLL TO REVEAL SPATIAL NODES
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 font-mono text-[9px] tracking-[0.34em] text-accent/90 bg-card/60 border border-border/40 px-3.5 py-1.5 rounded-full backdrop-blur-sm shadow-lg">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            <span>SELECT A SPATIAL NODE</span>
          </div>
        )}
      </div>
    </ApplicationShell>
  );
}
