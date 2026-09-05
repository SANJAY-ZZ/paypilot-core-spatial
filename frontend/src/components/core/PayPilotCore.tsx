import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { coreProgress, stageAmount, easeOut } from "@/lib/core-progress";

const IVORY = new THREE.Color("#efe7dc");
const EMBER = new THREE.Color("#e2593a");
const STEEL = new THREE.Color("#8b8f96");

/**
 * The PayPilot Core: an abstract financial intelligence engine built from
 * concentric geometric layers, orbital rings, a connected point lattice and
 * a soft internal glow.
 */
export function PayPilotCore() {
  const group = useRef<THREE.Group>(null);
  const inner = useRef<THREE.Group>(null);
  const shell = useRef<THREE.Mesh>(null);
  const ringA = useRef<THREE.Group>(null);
  const ringB = useRef<THREE.Group>(null);
  const ringC = useRef<THREE.Group>(null);
  const lattice = useRef<THREE.Points>(null);
  const glow = useRef<THREE.Mesh>(null);

  const latticeGeometry = useMemo(() => {
    const count = 420;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      // fibonacci sphere, jittered across three shells
      const shellRadius = 0.85 + (i % 3) * 0.32;
      const y = 1 - (i / (count - 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = Math.PI * (3 - Math.sqrt(5)) * i;
      positions[i * 3] = Math.cos(theta) * r * shellRadius;
      positions[i * 3 + 1] = y * shellRadius;
      positions[i * 3 + 2] = Math.sin(theta) * r * shellRadius;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geo;
  }, []);

  const chordGeometry = useMemo(() => {
    // thin internal data pathways connecting lattice points through the core
    const pts: number[] = [];
    const rand = mulberry(7);
    for (let i = 0; i < 46; i++) {
      const a = randomOnSphere(rand, 1.05);
      const b = randomOnSphere(rand, 1.05);
      const curve = new THREE.QuadraticBezierCurve3(
        a,
        new THREE.Vector3().addVectors(a, b).multiplyScalar(0.22),
        b,
      );
      const sampled = curve.getPoints(18);
      for (let j = 0; j < sampled.length - 1; j++) {
        const s0 = sampled[j]!;
        const s1 = sampled[j + 1]!;
        pts.push(s0.x, s0.y, s0.z);
        pts.push(s1.x, s1.y, s1.z);
      }

    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pts), 3));
    return geo;
  }, []);

  useFrame((state, delta) => {
    const p = coreProgress.eased;
    const appear = stageAmount(p, 0, 0.18);
    const activate = stageAmount(p, 0.16, 0.42);
    const t = state.clock.elapsedTime;
    const speed = coreProgress.reducedMotion ? 0.15 : 1;

    if (group.current) {
      const s = 0.35 + easeOut(appear) * 0.65;
      group.current.scale.setScalar(s);
      group.current.rotation.y += delta * (0.06 + activate * 0.16) * speed;
      group.current.rotation.x = Math.sin(t * 0.12) * 0.08 * speed;
    }
    if (inner.current) {
      inner.current.rotation.y -= delta * (0.12 + activate * 0.4) * speed;
      inner.current.rotation.z += delta * 0.05 * speed;
    }
    if (ringA.current) ringA.current.rotation.z += delta * 0.18 * speed;
    if (ringB.current) ringB.current.rotation.y += delta * 0.24 * speed;
    if (ringC.current) ringC.current.rotation.x -= delta * 0.13 * speed;

    if (shell.current) {
      const m = shell.current.material as THREE.MeshBasicMaterial;
      m.opacity = 0.0;
    }
    if (glow.current) {
      const m = glow.current.material as THREE.MeshBasicMaterial;
      m.opacity = (0.04 + activate * 0.06) * (0.85 + Math.sin(t * 1.1) * 0.15);
    }
    if (lattice.current) {
      const m = lattice.current.material as THREE.PointsMaterial;
      m.opacity = 0.15 + activate * 0.5;
      lattice.current.rotation.y += delta * 0.05 * speed;
    }
  });

  return (
    <group ref={group}>
      {/* internal glow */}
      <mesh ref={glow}>
        <sphereGeometry args={[0.52, 32, 32]} />
        <meshBasicMaterial color={EMBER} transparent opacity={0.05} depthWrite={false} />
      </mesh>

      {/* nucleus */}
      <mesh>
        <icosahedronGeometry args={[0.38, 1]} />
        <meshStandardMaterial
          color="#15161a"
          emissive={EMBER}
          emissiveIntensity={0.28}
          roughness={0.35}
          metalness={0.85}
          flatShading
        />
      </mesh>

      {/* concentric transparent layers */}
      <group ref={inner}>
        <mesh>
          <icosahedronGeometry args={[0.72, 1]} />
          <meshBasicMaterial color={STEEL} wireframe transparent opacity={0.22} />
        </mesh>
        <mesh rotation={[0.6, 0.4, 0]}>
          <octahedronGeometry args={[1.04, 0]} />
          <meshBasicMaterial color={IVORY} wireframe transparent opacity={0.12} />
        </mesh>
        <lineSegments geometry={chordGeometry}>
          <lineBasicMaterial color={EMBER} transparent opacity={0.16} />
        </lineSegments>
      </group>

      <mesh ref={shell}>
        <sphereGeometry args={[1.28, 48, 48]} />
        <meshBasicMaterial
          color={IVORY}
          transparent
          opacity={0.02}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>

      {/* connected point lattice */}
      <points ref={lattice} geometry={latticeGeometry}>
        <pointsMaterial
          color={IVORY}
          size={0.018}
          transparent
          opacity={0.4}
          sizeAttenuation
          depthWrite={false}
        />
      </points>

      {/* orbital rings */}
      <group ref={ringA} rotation={[Math.PI / 2.1, 0, 0]}>
        <mesh>
          <torusGeometry args={[1.55, 0.004, 8, 220]} />
          <meshBasicMaterial color={IVORY} transparent opacity={0.35} />
        </mesh>
        <mesh position={[1.55, 0, 0]}>
          <sphereGeometry args={[0.028, 12, 12]} />
          <meshBasicMaterial color={EMBER} />
        </mesh>
      </group>
      <group ref={ringB} rotation={[0.5, 0, Math.PI / 3]}>
        <mesh>
          <torusGeometry args={[1.9, 0.003, 8, 220]} />
          <meshBasicMaterial color={STEEL} transparent opacity={0.3} />
        </mesh>
        <mesh position={[0, 1.9, 0]}>
          <sphereGeometry args={[0.022, 12, 12]} />
          <meshBasicMaterial color={IVORY} />
        </mesh>
      </group>
      <group ref={ringC} rotation={[Math.PI / 2.6, 0.8, 0]}>
        <mesh>
          <torusGeometry args={[2.25, 0.0025, 8, 240]} />
          <meshBasicMaterial color={IVORY} transparent opacity={0.16} />
        </mesh>
      </group>
    </group>
  );
}

function mulberry(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function randomOnSphere(rand: () => number, radius: number) {
  const u = rand() * 2 - 1;
  const theta = rand() * Math.PI * 2;
  const r = Math.sqrt(1 - u * u);
  return new THREE.Vector3(r * Math.cos(theta), u, r * Math.sin(theta)).multiplyScalar(radius);
}
