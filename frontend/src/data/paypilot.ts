export interface CoreNodeData {
  id: string;
  label: string;
  metric: string;
  metricLabel: string;
  route: string;
  /** position in 3D space around the core */
  position: [number, number, number];
  /** emergence order in the scroll choreography (0..1) */
  order: number;
}

export interface SystemIndicator {
  label: string;
  value: string;
}

export const CORE_NODES: CoreNodeData[] = [
  {
    id: "revenue",
    label: "REVENUE",
    metric: "₹8.42L",
    metricLabel: "THIS MONTH",
    route: "/dashboard",
    position: [4.6, 1.35, 0.6],
    order: 0,
  },
  {
    id: "customers",
    label: "CUSTOMERS",
    metric: "1,024",
    metricLabel: "ACTIVE",
    route: "/customers",
    position: [3.5, -1.75, -2.1],
    order: 1,
  },
  {
    id: "opportunities",
    label: "OPPORTUNITIES",
    metric: "₹73,420",
    metricLabel: "RECOVERABLE",
    route: "/opportunities",
    position: [-4.4, 1.9, -1.2],
    order: 2,
  },
  {
    id: "copilot",
    label: "AI COPILOT",
    metric: "94%",
    metricLabel: "CONFIDENCE",
    route: "/copilot",
    position: [-3.3, -0.35, 2.4],
    order: 3,
  },
  {
    id: "guardian",
    label: "GUARDIAN",
    metric: "17 BLOCKED",
    metricLabel: "LAST 24H",
    route: "/guardian",
    position: [1.2, 3.05, -2.6],
    order: 4,
  },
  {
    id: "execution",
    label: "EXECUTION",
    metric: "42 RUNS",
    metricLabel: "AUTOMATED",
    route: "/actions",
    position: [-1.6, -2.95, 1.4],
    order: 5,
  },
  {
    id: "audit",
    label: "AUDIT",
    metric: "100%",
    metricLabel: "TRACEABLE",
    route: "/audit",
    position: [-2.2, 2.5, 2.6],
    order: 6,
  },
  {
    id: "commerce",
    label: "AI COMMERCE",
    metric: "8 AGENTS",
    metricLabel: "LIVE",
    route: "/commerce",
    position: [2.4, 0.9, 3.3],
    order: 7,
  },
];

export const SYSTEM_INDICATORS: SystemIndicator[] = [
  { label: "AI CONFIDENCE", value: "94%" },
  { label: "OPPORTUNITIES", value: "27" },
  { label: "RECOVERABLE", value: "₹73,420" },
];

export const HERO = {
  titleLines: ["YOUR REVENUE", "IS TALKING."],
  supporting:
    "PayPilot continuously discovers and evaluates revenue opportunities across your merchant ecosystem.",
  status: "PAYPILOT CORE / ONLINE",
};

export const MODULE_TITLES: Record<string, string> = {
  "/dashboard": "REVENUE",
  "/customers": "CUSTOMERS",
  "/opportunities": "OPPORTUNITIES",
  "/copilot": "AI COPILOT",
  "/guardian": "GUARDIAN",
  "/actions": "EXECUTION",
  "/audit": "AUDIT",
  "/commerce": "AI COMMERCE",
};
