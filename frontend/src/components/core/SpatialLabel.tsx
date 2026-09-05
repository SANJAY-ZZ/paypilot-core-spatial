import { Html } from "@react-three/drei";

interface SpatialLabelProps {
  label: string;
  metric: string;
  metricLabel: string;
  active: boolean;
  dimmed: boolean;
  visible: boolean;
}

/** Floating typographic marker attached to a spatial node (no cards). */
export function SpatialLabel({
  label,
  metric,
  metricLabel,
  active,
  dimmed,
  visible,
}: SpatialLabelProps) {
  return (
    <Html
      center={false}
      distanceFactor={7}
      position={[0.16, 0.16, 0]}
      style={{ pointerEvents: "none" }}
      zIndexRange={[20, 0]}
    >
      <div
        className="select-none whitespace-nowrap transition-all duration-500"
        style={{
          opacity: visible ? (dimmed ? 0.28 : 1) : 0,
          transform: `translateY(${visible ? 0 : 8}px)`,
        }}
      >
        <div className="flex items-center gap-2">
          <span
            className={`h-px w-6 transition-all duration-500 ${
              active ? "bg-accent" : "bg-muted-foreground/50"
            }`}
          />
          <span
            className={`font-mono text-[11px] tracking-[0.22em] transition-colors duration-500 ${
              active ? "text-foreground" : "text-muted-foreground"
            }`}
          >
            {label}
          </span>
        </div>
        <div
          className="overflow-hidden pl-8 transition-all duration-500"
          style={{
            maxHeight: active ? 40 : 0,
            opacity: active ? 1 : 0,
          }}
        >
          <div className="pt-1 font-mono text-[15px] tracking-tight text-accent">{metric}</div>
          <div className="font-mono text-[9px] tracking-[0.3em] text-muted-foreground">
            {metricLabel}
          </div>
        </div>
      </div>
    </Html>
  );
}
