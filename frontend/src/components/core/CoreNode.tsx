import { useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { CoreNodeData } from "@/data/paypilot";
import { coreProgress, stageAmount, easeOut } from "@/lib/core-progress";
import { SpatialLabel } from "./SpatialLabel";

interface CoreNodeProps {
  node: CoreNodeData;
  index: number;
  total: number;
  hovered: boolean;
  selected: boolean;
  anySelected: boolean;
  onHover: (id: string | null) => void;
  onSelect: (node: CoreNodeData) => void;
}

export function CoreNode({
  node,
  index,
  total,
  hovered,
  selected,
  anySelected,
  onHover,
  onSelect,
}: CoreNodeProps) {
  const group = useRef<THREE.Group>(null);
  const marker = useRef<THREE.Mesh>(null);
  const halo = useRef<THREE.Mesh>(null);
  const [emerged, setEmerged] = useState(false);

  const home = new THREE.Vector3(...node.position);

  useFrame((state, delta) => {
    if (!group.current) return;
    const p = coreProgress.eased;
    const start = 0.55 + (index / total) * 0.22;
    const reveal = easeOut(stageAmount(p, start, start + 0.16));
    if (reveal > 0.02 !== emerged) setEmerged(reveal > 0.02);

    const t = state.clock.elapsedTime;
    const drift = coreProgress.reducedMotion ? 0 : Math.sin(t * 0.5 + index) * 0.06;

    const dim = anySelected && !selected;
    const pull = selected ? 0.55 : dim ? 1.22 : 1;

    const target = home.clone().multiplyScalar(pull * (0.55 + reveal * 0.45));
    target.y += drift;
    group.current.position.lerp(target, 1 - Math.pow(0.001, delta));

    const scale = reveal * (selected ? 1.9 : hovered ? 1.35 : 1) * (dim ? 0.75 : 1);
    group.current.scale.lerp(
      new THREE.Vector3(scale, scale, scale),
      1 - Math.pow(0.002, delta),
    );

    if (marker.current) {
      marker.current.rotation.y += delta * (hovered || selected ? 0.9 : 0.25);
      marker.current.rotation.x += delta * 0.12;
      const m = marker.current.material as THREE.MeshStandardMaterial;
      m.emissiveIntensity = THREE.MathUtils.lerp(
        m.emissiveIntensity,
        selected ? 2.4 : hovered ? 1.6 : dim ? 0.18 : 0.6,
        1 - Math.pow(0.01, delta),
      );
    }
    if (halo.current) {
      const m = halo.current.material as THREE.MeshBasicMaterial;
      m.opacity = THREE.MathUtils.lerp(
        m.opacity,
        selected ? 0.3 : hovered ? 0.2 : dim ? 0.02 : 0.07,
        1 - Math.pow(0.01, delta),
      );
      halo.current.lookAt(state.camera.position);
    }
  });

  return (
    <group ref={group} scale={0.001}>
      <mesh ref={halo}>
        <circleGeometry args={[0.11, 40]} />
        <meshBasicMaterial color="#e2593a" transparent opacity={0.1} depthWrite={false} />
      </mesh>

      {/* generous invisible hit area */}
      <mesh
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(node.id);
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={(e) => {
          e.stopPropagation();
          onHover(null);
          document.body.style.cursor = "auto";
        }}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
      >
        <sphereGeometry args={[0.42, 12, 12]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>

      <mesh ref={marker}>
        <octahedronGeometry args={[0.15, 0]} />
        <meshStandardMaterial
          color="#1b1c20"
          emissive="#e2593a"
          emissiveIntensity={0.6}
          metalness={0.9}
          roughness={0.25}
          flatShading
        />
      </mesh>

      {/* thin spatial marker cross */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[
              new Float32Array([
                -0.3, 0, 0, 0.3, 0, 0, 0, -0.3, 0, 0, 0.3, 0, 0, 0, -0.3, 0, 0, 0.3,
              ]),
              3,
            ]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#8b8f96" transparent opacity={0.28} />
      </lineSegments>

      <SpatialLabel
        label={node.label}
        metric={node.metric}
        metricLabel={node.metricLabel}
        active={hovered || selected}
        dimmed={anySelected && !selected}
        visible={emerged}
      />
    </group>
  );
}
