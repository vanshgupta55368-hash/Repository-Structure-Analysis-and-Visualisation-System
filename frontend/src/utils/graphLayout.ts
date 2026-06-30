import dagre from "dagre";
import type { Edge, Node } from "reactflow";

const NODE_WIDTH = 220;
const NODE_HEIGHT = 70;

export function layoutGraph(
  nodes: Node[],
  edges: Edge[],
  direction: "TB" | "LR" = "LR"
) {
  const isHorizontal = direction === "LR";

  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 120,
    marginx: 20,
    marginy: 20,
  });

  for (const node of nodes) {
    graph.setNode(node.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });
  }

  for (const edge of edges) {
    if (edge.source && edge.target) {
      graph.setEdge(edge.source, edge.target);
    }
  }

  dagre.layout(graph);

  const layoutedNodes = nodes.map((node) => {
    const pos = graph.node(node.id);

    // Safety fallback so the app never crashes if Dagre misses a node.
    if (!pos || typeof pos.x !== "number" || typeof pos.y !== "number") {
      return {
        ...node,
        sourcePosition: isHorizontal ? "right" : "bottom",
        targetPosition: isHorizontal ? "left" : "top",
      };
    }

    return {
      ...node,
      sourcePosition: isHorizontal ? "right" : "bottom",
      targetPosition: isHorizontal ? "left" : "top",
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });

  return {
    nodes: layoutedNodes,
    edges,
  };
}