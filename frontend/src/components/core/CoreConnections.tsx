import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { CORE_NODES } from "@/data/paypilot";
import { coreProgress, stageAmount } from "@/lib/core-progress";

const SEGMENTS = 26;
const FLOW_PER_PATH = 3;

/** Thin curved pathways from the Core to each node, with travelling data motes. */
export function CoreConnections({
  hoveredId,
  selectedId,
}: {
  hoveredId: string | null;
  selectedId: string | null;
}) {
  const linesRef = useRef<THREE.LineSegments>(null);
  const flowRef = useRef<THREE.Points>(null);

  const { curves, lineGeometry, flowGeometry } = useMemo(() => {
    const curves = CORE_NODES.map((n) => {
      const end = new THREE.Vector3(...n.position);
      const mid = end
        .clone()
        .multiplyScalar(0.5)
        .add(new THREE.Vector3(end.z * 0.12, 0.35, -end.x * 0.12));
      return new THREE.QuadraticBezierCurve3(new THREE.Vector3(0, 0, 0), mid, end);
    });

    const pos: number[] = [];
    const col: number[] = [];
    curves.forEach(() => {
      for (let i = 0; i < SEGMENTS; i++) {
        pos.push(0, 0, 0, 0, 0, 0);
        col.push(0, 0, 0, 0, 0, 0);
      }
    });
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
    lineGeometry.setAttribute("color", new THREE.BufferAttribute(new Float32Array(col), 3));

    const flowGeometry = new THREE.BufferGeometry();
    flowGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(new Float32Array(curves.length * FLOW_PER_PATH * 3), 3),
    );
    return { curves, lineGeometry, flowGeometry };
  }, []);

  useFrame((state) => {
    const p = coreProgress.eased;
    const pathAmount = stageAmount(p, 0.38, 0.62);
    const t = state.clock.elapsedTime * (coreProgress.reducedMotion ? 0.15 : 1);

    const linePos = lineGeometry.getAttribute("position") as THREE.BufferAttribute;
    const lineCol = lineGeometry.getAttribute("color") as THREE.BufferAttribute;
    const flowPos = flowGeometry.getAttribute("position") as THREE.BufferAttribute;

    const base = new THREE.Color("#6f747c");
    const hot = new THREE.Color("#e2593a");
    const tmp = new THREE.Color();
    const v = new THREE.Vector3();

    let li = 0;
    curves.forEach((curve, ci) => {
      const node = CORE_NODES[ci]!;

      const active = hoveredId === node.id || selectedId === node.id;
      const dim = selectedId !== null && selectedId !== node.id;

      const nodeStart = 0.55 + (ci / CORE_NODES.length) * 0.22;
      const grow = Math.max(pathAmount * 0.7, stageAmount(p, 0.4, nodeStart + 0.1));
      const intensity = (dim ? 0.15 : active ? 1 : 0.4) * grow;
      tmp.copy(active ? hot : base).multiplyScalar(intensity);

      for (let s = 0; s < SEGMENTS; s++) {
        const a = (s / SEGMENTS) * grow;
        const b = ((s + 1) / SEGMENTS) * grow;
        curve.getPoint(a, v);
        linePos.setXYZ(li, v.x, v.y, v.z);
        lineCol.setXYZ(li, tmp.r, tmp.g, tmp.b);
        li++;
        curve.getPoint(b, v);
        linePos.setXYZ(li, v.x, v.y, v.z);
        lineCol.setXYZ(li, tmp.r, tmp.g, tmp.b);
        li++;
      }

      for (let f = 0; f < FLOW_PER_PATH; f++) {
        const phase = ((t * 0.16 + f / FLOW_PER_PATH + ci * 0.13) % 1) * grow;
        curve.getPoint(phase, v);
        const idx = ci * FLOW_PER_PATH + f;
        if (grow < 0.05 || dim) flowPos.setXYZ(idx, 0, -999, 0);
        else flowPos.setXYZ(idx, v.x, v.y, v.z);
      }
    });

    linePos.needsUpdate = true;
    lineCol.needsUpdate = true;
    flowPos.needsUpdate = true;

    if (flowRef.current) {
      const m = flowRef.current.material as THREE.PointsMaterial;
      m.opacity = 0.25 + pathAmount * 0.55;
    }
  });

  return (
    <group>
      <lineSegments ref={linesRef} geometry={lineGeometry}>
        <lineBasicMaterial vertexColors transparent opacity={0.85} depthWrite={false} />
      </lineSegments>
      <points ref={flowRef} geometry={flowGeometry}>
        <pointsMaterial
          color="#e8b39c"
          size={0.035}
          sizeAttenuation
          transparent
          opacity={0.6}
          depthWrite={false}
        />
      </points>
    </group>
  );
}
