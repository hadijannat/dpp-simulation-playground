import ReactFlow, { Background, Controls, Node } from "reactflow";
import "reactflow/dist/style.css";

const initialNodes: Node[] = [
  { id: "start", position: { x: 0, y: 0 }, data: { label: "Start" }, type: "input" },
  { id: "step", position: { x: 200, y: 0 }, data: { label: "Step" } },
  { id: "done", position: { x: 400, y: 0 }, data: { label: "Complete" }, type: "output" },
];

export default function SimulationCanvas() {
  return (
    <div style={{ height: 300, border: "1px solid #e2e8f0", borderRadius: 8 }}>
      <ReactFlow nodes={initialNodes} edges={[]} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
