import React from "react";
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
  selectedNodeId?: string | null;
  onNodeClick?: (event: any, node: Node) => void;
  onPaneClick?: () => void;
};

const laneLabels = [
  "API",
  "SERVICES",
  "MODELS",
  "CORE",
  "UTILS",
  "PARSERS",
  "OTHER",
];

export default function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
  onPaneClick,
}: GraphCanvasProps) {
  return (
    <div className="graph-card">
      <div className="graph-header">
        <div>
          <h2>Dependency graph</h2>
          <p>Click a node to load the AI file summary.</p>
        </div>

        <div className="graph-legend">
          <span>
            <i className="legend-dot legend-api" /> API
          </span>
          <span>
            <i className="legend-dot legend-services" /> SERVICES
          </span>
          <span>
            <i className="legend-dot legend-models" /> MODELS
          </span>
          <span>
            <i className="legend-dot legend-core" /> CORE
          </span>
          <span>
            <i className="legend-dot legend-utils" /> UTILS
          </span>
          <span>
            <i className="legend-dot legend-parsers" /> PARSERS
          </span>
        </div>
      </div>
<div className="complexity-legend">
  <h4>Complexity</h4>

  <span><i className="legend-border low" /> Low (0–5)</span>

  <span><i className="legend-border medium" /> Medium (6–11)</span>

  <span><i className="legend-border high" /> High (12–19)</span>

  <span><i className="legend-border critical" /> Critical (20+)</span>
</div>
      <div className="lane-header-row">
        {laneLabels.map((label) => (
          <div key={label} className="lane-header">
            {label}
          </div>
        ))}
      </div>

      <div className="graph-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}