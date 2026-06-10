import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

type GraphCanvasProps = {
  nodes: Node[];
  edges: Edge[];
};

export default function GraphCanvas({ nodes, edges }: GraphCanvasProps) {
  return (
    <div className="graph-card">
      <div className="graph-header">
        <div>
          <h2>Dependency graph</h2>
          <p>Drag nodes, zoom, and explore repository structure.</p>
        </div>
      </div>

      <div className="graph-container">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}