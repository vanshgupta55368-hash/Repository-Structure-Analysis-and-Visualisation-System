import { FormEvent, useEffect, useMemo, useState } from "react";
import { analyzeRepository, getHealth } from "./api/backend";
import type { AnalysisResponse, HealthResponse } from "./types/api";
import GraphCanvas from "./components/GraphCanvas";
import { layoutGraph } from "./utils/graphLayout";
import "./App.css";

const DEFAULT_REPO_PATH =
  "C:\\Users\\Lenovo\\repo-visualizer\\repo-visualizer\\backend";

function StatCard({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string | number;
  sublabel?: string;
}) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {sublabel ? <div className="metric-sublabel">{sublabel}</div> : null}
    </div>
  );
}

function toReactFlowNodes(analysis: AnalysisResponse) {
  const columns = 4;
  const horizontalGap = 280;
  const verticalGap = 150;

  return analysis.nodes.map((node, index) => {
    const row = Math.floor(index / columns);
    const col = index % columns;

    const id = String(node.id);
    const label =
      typeof node.label === "string" ? node.label : String(node.id ?? "file");

    const language =
      typeof (node as any).language === "string"
        ? String((node as any).language)
        : "unknown";

    const backgroundByLanguage: Record<string, string> = {
      python: "#1e3a8a",
      cpp: "#0f766e",
      markdown: "#334155",
      text: "#334155",
      unknown: "#1e293b",
    };

    return {
      id,
      position: {
        x: col * horizontalGap,
        y: row * verticalGap,
      },
      data: {
        label,
        language,
      },
      type: "default",
      style: {
        background: backgroundByLanguage[language] ?? "#1e293b",
        color: "#e2e8f0",
        border: "1px solid rgba(56, 189, 248, 0.28)",
        borderRadius: "14px",
        padding: "10px 12px",
        minWidth: "180px",
        boxShadow: "0 10px 30px rgba(2, 6, 23, 0.25)",
        fontSize: "12px",
      },
    };
  });
}

function toReactFlowEdges(analysis: AnalysisResponse) {
  return analysis.edges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    animated: false,
    style: {
      stroke: "#38bdf8",
      strokeWidth: 1.5,
    },
    label: edge.relation,
    labelStyle: {
      fill: "#cbd5e1",
      fontSize: 12,
    },
  }));
}

function App() {
  const [repoPath, setRepoPath] = useState(DEFAULT_REPO_PATH);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const data = await getHealth();
        setHealth(data);
      } catch {
        setError("Failed to connect to backend.");
      } finally {
        setLoadingHealth(false);
      }
    };

    loadHealth();
  }, []);

  const filteredAnalysis = useMemo(() => {
    if (!analysis) return null;

    const hiddenFiles = new Set([
      ".env",
      "README.md",
      "requirements.txt",
    ]);

    const visibleNodes = analysis.nodes.filter((node) => {
      const id = String(node.id);
      return (
        !hiddenFiles.has(id) &&
        !id.endsWith("__init__.py")
      );
    });

    const visibleNodeIds = new Set(visibleNodes.map((node) => String(node.id)));

    const visibleEdges = analysis.edges.filter(
      (edge) =>
        visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );

    return {
      ...analysis,
      nodes: visibleNodes,
      edges: visibleEdges,
    };
  }, [analysis]);

  const reactFlowNodes = useMemo(() => {
    if (!filteredAnalysis) return [];
    const nodes = toReactFlowNodes(filteredAnalysis);
    return layoutGraph(nodes, toReactFlowEdges(filteredAnalysis), "TB").nodes;
  }, [filteredAnalysis]);

  const reactFlowEdges = useMemo(() => {
    if (!filteredAnalysis) return [];
    return toReactFlowEdges(filteredAnalysis);
  }, [filteredAnalysis]);

  const topDependencies = useMemo(() => {
    if (!analysis) return [];
    return Object.entries(analysis.dependency_map)
      .slice(0, 8)
      .map(([file, deps]) => ({
        file,
        deps: deps.slice(0, 4),
      }));
  }, [analysis]);

  const handleAnalyze = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoadingAnalysis(true);

    try {
      const result = await analyzeRepository(repoPath);
      setAnalysis(result);
    } catch (err: any) {
      setAnalysis(null);
      setError(err?.response?.data?.detail || err?.message || "Analysis failed.");
    } finally {
      setLoadingAnalysis(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="container">
        <section className="hero">
          <div>
            <p className="eyebrow">Phase 1 · Backend connected dashboard</p>
            <h1>Repo Visualizer</h1>
            <p className="subtitle">
              Analyze a repository, inspect metrics, and explore its dependency graph.
            </p>
          </div>

          <div className={`status-chip ${health ? "ok" : "warn"}`}>
            {loadingHealth
              ? "Checking backend..."
              : health
              ? "Backend connected"
              : "Backend offline"}
          </div>
        </section>

        <form className="control-card" onSubmit={handleAnalyze}>
          <label className="field-label" htmlFor="repoPath">
            Repository path
          </label>

          <div className="input-row">
            <input
              id="repoPath"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              placeholder="C:\\Users\\Lenovo\\repo-visualizer\\repo-visualizer\\backend"
            />
            <button type="submit" disabled={loadingHealth || loadingAnalysis}>
              {loadingAnalysis ? "Analyzing..." : "Analyze repository"}
            </button>
          </div>

          {error ? <p className="error">{error}</p> : null}
        </form>

        {health ? (
          <section className="mini-banner">
            <span>API:</span> {health.app_name} · {health.version} · debug{" "}
            {String(health.debug)}
          </section>
        ) : null}

        {filteredAnalysis ? (
          <>
            <section className="stats-grid">
              <StatCard label="Files" value={filteredAnalysis.stats.total_files} sublabel="scanned" />
              <StatCard label="LOC" value={filteredAnalysis.stats.total_loc} sublabel="total lines" />
              <StatCard
                label="Code Lines"
                value={filteredAnalysis.stats.total_code_lines}
                sublabel="non-empty logic"
              />
              <StatCard
                label="Avg Complexity"
                value={filteredAnalysis.stats.average_complexity.toFixed(2)}
                sublabel="per file"
              />
            </section>

            <section className="two-column">
              <div className="panel">
                <h2>Graph insights</h2>

                <div className="insight-grid">
                  <div>
                    <div className="insight-label">Isolated files</div>
                    <div className="insight-value">
                      {filteredAnalysis.graph_insights.isolated_files.length}
                    </div>
                  </div>
                  <div>
                    <div className="insight-label">Cycles</div>
                    <div className="insight-value">
                      {filteredAnalysis.graph_insights.cycles.length}
                    </div>
                  </div>
                  <div>
                    <div className="insight-label">Components</div>
                    <div className="insight-value">
                      {filteredAnalysis.graph_insights.connected_components.length}
                    </div>
                  </div>
                  <div>
                    <div className="insight-label">Edges</div>
                    <div className="insight-value">{filteredAnalysis.edges.length}</div>
                  </div>
                </div>

                <h3>Top complex files</h3>
                <div className="pill-list">
                  {filteredAnalysis.stats.top_complex_files.slice(0, 5).map((item) => (
                    <span className="pill" key={item.file}>
                      {item.file} · {item.complexity}
                    </span>
                  ))}
                </div>
              </div>

              <div className="panel">
                <h2>Dependency preview</h2>
                <p className="muted">
                  A quick look at the first few file-to-file dependency entries.
                </p>

                <div className="dependency-list">
                  {topDependencies.map(({ file, deps }) => (
                    <div className="dependency-item" key={file}>
                      <div className="dependency-file">{file}</div>
                      <div className="dependency-deps">
                        {deps.length > 0
                          ? deps.join(", ")
                          : "No direct dependencies detected"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <GraphCanvas nodes={reactFlowNodes} edges={reactFlowEdges} />

            <section className="panel raw-panel">
              <h2>Repository hash</h2>
              <code>{filteredAnalysis.repo_hash}</code>
            </section>
          </>
        ) : null}
      </div>
    </div>
  );
}

export default App;