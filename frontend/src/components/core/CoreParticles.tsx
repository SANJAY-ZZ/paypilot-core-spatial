import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { coreProgress, stageAmount } from "@/lib/core-progress";

/** Ambient volumetric dust giving the scene depth and parallax. */
export function CoreParticles({ count = 900 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null);

  const geometry = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      const r = 3 + Math.random() * 9;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.cos(phi) * 0.55;
      positions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
      sizes[i] = Math.random();
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1));
    return geo;
  }, [count]);

  useFrame((state, delta) => {
    if (!ref.current) return;
    const p = coreProgress.eased;
    const amount = stageAmount(p, 0.3, 0.6);
    const speed = coreProgress.reducedMotion ? 0.1 : 1;
    ref.current.rotation.y += delta * 0.012 * speed;
    ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.05) * 0.03;
    const m = ref.current.material as THREE.PointsMaterial;
    m.opacity = 0.08 + amount * 0.32;
  });

  return (
    <points ref={ref} geometry={geometry}>
      <pointsMaterial
        color="#cfc6b8"
        size={0.022}
        sizeAttenuation
        transparent
        opacity={0.1}
        depthWrite={false}
      />
    </points>
  );
}
