import ReactFlow, { Background, Controls, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";

interface StepNode {
  action: string;
}

export default function SimulationCanvas({
  steps,
  completed,
}: {
  steps: StepNode[];
  completed: number[];
}) {
  const nodes: Node[] = steps.map((step, idx) => ({
    id: `step-${idx}`,
    position: { x: idx * 200, y: 0 },
    data: { label: `${idx + 1}. ${step.action}` },
    style: {
      border: "1px solid #cbd5f5",
      padding: 10,
      background: completed.includes(idx) ? "#dcfce7" : "#fff",
      borderRadius: 12,
    },
  }));

  const edges: Edge[] = steps.slice(1).map((_, idx) => ({
    id: `edge-${idx}`,
    source: `step-${idx}`,
    target: `step-${idx + 1}`,
  }));

  return (
    <div style={{ height: 260, border: "1px solid #e2e8f0", borderRadius: 12 }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
