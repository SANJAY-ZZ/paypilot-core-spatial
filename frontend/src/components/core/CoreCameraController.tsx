import { useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import type { CoreNodeData } from "@/data/paypilot";
import { coreProgress, easeOut, stageAmount } from "@/lib/core-progress";

/**
 * Camera choreography: the scroll sequence drives a dolly path around the Core,
 * and selecting a node flies the camera toward it.
 */
export function CoreCameraController({ selected }: { selected: CoreNodeData | null }) {
  const { camera, pointer } = useThree();
  const target = useRef(new THREE.Vector3(0, 0, 0));
  const desired = useRef(new THREE.Vector3(0, 0, 14));

  useFrame((_, delta) => {
    const p = coreProgress.eased;

    // Stage-based dolly: far and high -> settled three-quarter view
    const intro = easeOut(stageAmount(p, 0, 0.3));
    const mid = easeOut(stageAmount(p, 0.3, 0.65));
    const wide = easeOut(stageAmount(p, 0.65, 1));

    const radius = 13.5 - intro * 4.2 - mid * 1.6 + wide * 2.6;
    const angle = -0.35 + intro * 0.28 + mid * 0.32 + wide * 0.22;
    const height = 2.6 - intro * 1.5 + mid * 0.4 + wide * 0.9;

    desired.current.set(Math.sin(angle) * radius, height, Math.cos(angle) * radius);
    target.current.set(0, 0, 0);

    if (selected) {
      const nodePos = new THREE.Vector3(...selected.position).multiplyScalar(0.55);
      const dir = nodePos.clone().normalize();
      desired.current.copy(nodePos.clone().add(dir.multiplyScalar(2.6)).add(new THREE.Vector3(0, 0.5, 0)));
      target.current.copy(nodePos);
    }

    // subtle parallax from pointer
    if (!coreProgress.reducedMotion) {
      desired.current.x += pointer.x * 0.55;
      desired.current.y += pointer.y * 0.35;
    }

    const k = 1 - Math.pow(selected ? 0.0008 : 0.006, delta);
    camera.position.lerp(desired.current, k);
    camera.lookAt(target.current);
  });

  return null;
}
