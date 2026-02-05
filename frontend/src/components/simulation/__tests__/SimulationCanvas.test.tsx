import { render } from "@testing-library/react";
import SimulationCanvas from "../SimulationCanvas";

/* ------------------------------------------------------------------ */
/*  Mock ReactFlow                                                    */
/* ------------------------------------------------------------------ */

// ReactFlow requires a browser-level resize observer and DOM measurements
// that jsdom does not provide. We mock the entire module to capture props.

let capturedNodes: Array<{
  id: string;
  data: { label: string };
  style: Record<string, string>;
}> = [];

vi.mock("reactflow", () => {
  const Background = () => null;
  const Controls = () => null;

  function ReactFlow(props: { nodes: typeof capturedNodes; edges: unknown[]; fitView?: boolean; children?: React.ReactNode }) {
    capturedNodes = props.nodes;
    return (
      <div data-testid="reactflow">
        {props.nodes.map((node) => (
          <div key={node.id} data-testid={node.id} data-style={JSON.stringify(node.style)}>
            {node.data.label}
          </div>
        ))}
      </div>
    );
  }

  return {
    __esModule: true,
    default: ReactFlow,
    Background,
    Controls,
  };
});

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

const sampleSteps = [
  { action: "aas.create" },
  { action: "compliance.check" },
  { action: "edc.negotiate" },
  { action: "edc.transfer" },
];

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("SimulationCanvas", () => {
  beforeEach(() => {
    capturedNodes = [];
  });

  it("renders a node for each story step", () => {
    const { getByTestId } = render(
      <SimulationCanvas steps={sampleSteps} completed={[]} />,
    );
    expect(getByTestId("step-0")).toBeInTheDocument();
    expect(getByTestId("step-1")).toBeInTheDocument();
    expect(getByTestId("step-2")).toBeInTheDocument();
    expect(getByTestId("step-3")).toBeInTheDocument();
  });

  it("renders the correct label for each node", () => {
    const { getByTestId } = render(
      <SimulationCanvas steps={sampleSteps} completed={[]} />,
    );
    expect(getByTestId("step-0")).toHaveTextContent("1. aas.create");
    expect(getByTestId("step-1")).toHaveTextContent("2. compliance.check");
    expect(getByTestId("step-2")).toHaveTextContent("3. edc.negotiate");
    expect(getByTestId("step-3")).toHaveTextContent("4. edc.transfer");
  });

  it("completed steps have completed background styling", () => {
    render(
      <SimulationCanvas steps={sampleSteps} completed={[0, 2]} />,
    );
    // Completed nodes should use the completed background CSS variable
    const completedNode0 = capturedNodes.find((n) => n.id === "step-0");
    const incompleteNode1 = capturedNodes.find((n) => n.id === "step-1");
    const completedNode2 = capturedNodes.find((n) => n.id === "step-2");

    expect(completedNode0?.style.background).toBe("var(--canvas-node-completed)");
    expect(incompleteNode1?.style.background).toBe("var(--canvas-node-bg)");
    expect(completedNode2?.style.background).toBe("var(--canvas-node-completed)");
  });

  it("non-completed steps have default background", () => {
    render(
      <SimulationCanvas steps={sampleSteps} completed={[0]} />,
    );
    const node1 = capturedNodes.find((n) => n.id === "step-1");
    const node2 = capturedNodes.find((n) => n.id === "step-2");
    const node3 = capturedNodes.find((n) => n.id === "step-3");

    expect(node1?.style.background).toBe("var(--canvas-node-bg)");
    expect(node2?.style.background).toBe("var(--canvas-node-bg)");
    expect(node3?.style.background).toBe("var(--canvas-node-bg)");
  });

  it("renders no nodes when steps array is empty", () => {
    render(<SimulationCanvas steps={[]} completed={[]} />);
    expect(capturedNodes).toHaveLength(0);
  });

  it("all steps completed shows all nodes with completed background", () => {
    render(
      <SimulationCanvas steps={sampleSteps} completed={[0, 1, 2, 3]} />,
    );
    for (const node of capturedNodes) {
      expect(node.style.background).toBe("var(--canvas-node-completed)");
    }
  });
});
