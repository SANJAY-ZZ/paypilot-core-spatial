import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { ApplicationShell } from "./ApplicationShell";

export function ModulePlaceholder({ title }: { title: string }) {
  return (
    <ApplicationShell>
      <main className="flex min-h-screen items-center">
        <div className="mx-auto w-full max-w-[1600px] px-10 pt-14">
          <Link
            to="/"
            className="inline-flex items-center gap-2 font-mono text-[10px] tracking-[0.32em] text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" strokeWidth={1.5} />
            CORE
          </Link>

          <h1 className="mt-10 font-display text-[56px] leading-none tracking-[-0.03em] text-foreground">
            {title}
          </h1>
          <div className="mt-8 h-px w-40 bg-accent/70" />
          <p className="mt-6 max-w-sm font-mono text-[10px] tracking-[0.28em] text-muted-foreground">
            MODULE PENDING
          </p>
        </div>
      </main>
    </ApplicationShell>
  );
}
