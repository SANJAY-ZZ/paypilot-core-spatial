import { useCallback, useState, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { CORE_NODES, type CoreNodeData } from "@/data/paypilot";
import { api } from "@/lib/api";
import { PayPilotCore } from "./PayPilotCore";
import { CoreNode } from "./CoreNode";
import { CoreConnections } from "./CoreConnections";
import { CoreParticles } from "./CoreParticles";
import { CoreCameraController } from "./CoreCameraController";

export default function CoreScene() {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState<string | null>(null);
  const [selected, setSelected] = useState<CoreNodeData | null>(null);

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });

  const { data: commerce } = useQuery({
    queryKey: ["commerce-readiness"],
    queryFn: () => api.getCommerceReadiness(),
  });

  // Dynamically map live backend data to spatial nodes while strictly preserving 3D positions and choreography
  const liveNodes = useMemo<CoreNodeData[]>(() => {
    return CORE_NODES.map((node) => {
      if (node.id === "revenue" && dashboard) {
        return {
          ...node,
          metric: `₹${(dashboard.total_revenue / 100000).toFixed(2)}L`,
          metricLabel: "GROSS REVENUE",
        };
      }
      if (node.id === "customers" && dashboard) {
        return {
          ...node,
          metric: dashboard.customer_count.toLocaleString("en-IN"),
          metricLabel: "VERIFIED BUYERS",
        };
      }
      if (node.id === "opportunities" && dashboard) {
        return {
          ...node,
          metric: `₹${dashboard.recoverable_revenue.toLocaleString("en-IN")}`,
          metricLabel: "RECOVERABLE",
        };
      }
      if (node.id === "execution" && dashboard) {
        return {
          ...node,
          metric: `${dashboard.ai_actions_today} RUNS`,
          metricLabel: "AUTOMATED",
        };
      }
      if (node.id === "commerce" && commerce) {
        return {
          ...node,
          metric: `${commerce.overall_score}/100`,
          metricLabel: "READINESS",
        };
      }
      return node;
    });
  }, [dashboard, commerce]);

  const handleSelect = useCallback(
    (node: CoreNodeData) => {
      if (selected?.id === node.id) return;
      setSelected(node);
      window.setTimeout(() => {
        navigate({ to: node.route });
      }, 1100);
    },
    [navigate, selected],
  );

  return (
    <Canvas
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }}
      camera={{ position: [0, 2.6, 14], fov: 42, near: 0.1, far: 100 }}
      onPointerMissed={() => setSelected(null)}
    >
      <color attach="background" args={["#0b0b0d"]} />
      <fog attach="fog" args={["#0b0b0d", 10, 26]} />

      <ambientLight intensity={0.35} />
      <pointLight position={[0, 0, 0]} intensity={3} color="#e2593a" distance={7} />
      <directionalLight position={[6, 8, 6]} intensity={0.8} color="#efe7dc" />
      <directionalLight position={[-7, -3, -5]} intensity={0.35} color="#5d6270" />

      <CoreParticles />
      <PayPilotCore />
      <CoreConnections hoveredId={hovered} selectedId={selected?.id ?? null} />

      {liveNodes.map((node, i) => (
        <CoreNode
          key={node.id}
          node={node}
          index={i}
          total={liveNodes.length}
          hovered={hovered === node.id}
          selected={selected?.id === node.id}
          anySelected={selected !== null}
          onHover={setHovered}
          onSelect={handleSelect}
        />
      ))}

      <CoreCameraController selected={selected} />
    </Canvas>
  );
}
