import { FormEvent, useEffect, useMemo, useState } from "react";
import { analyzeRepository, getHealth } from "./api/backend";
import type { AnalysisResponse, HealthResponse } from "./types/api";
import StatCard from "./components/StatCard";
import "./App.css";

const DEFAULT_REPO_PATH =
  "C:\\Users\\Lenovo\\repo-visualizer\\repo-visualizer\\backend";

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
      } catch (err) {
        setError("Failed to connect to backend.");
      } finally {
        setLoadingHealth(false);
      }
    };

    loadHealth();
  }, []);

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
              Analyze a repository, inspect metrics, and prepare the graph data for React Flow.
            </p>
          </div>

          <div className={`status-chip ${health ? "ok" : "warn"}`}>
            {loadingHealth ? "Checking backend..." : health ? "Backend connected" : "Backend offline"}
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

          {error && <p className="error">{error}</p>}
        </form>

        {health && (
          <section className="mini-banner">
            <span>API:</span> {health.app_name} · {health.version} · debug {String(health.debug)}
          </section>
        )}

        {analysis && (
          <>
            <section className="stats-grid">
              <StatCard label="Files" value={analysis.stats.total_files} sublabel="scanned" />
              <StatCard label="LOC" value={analysis.stats.total_loc} sublabel="total lines" />
              <StatCard label="Code Lines" value={analysis.stats.total_code_lines} sublabel="non-empty logic" />
              <StatCard
                label="Avg Complexity"
                value={analysis.stats.average_complexity.toFixed(2)}
                sublabel="per file"
              />
            </section>

            <section className="two-column">
              <div className="panel">
                <h2>Graph insights</h2>

                <div className="insight-grid">
                  <div>
                    <div className="insight-label">Isolated files</div>
                    <div className="insight-value">{analysis.graph_insights.isolated_files.length}</div>
                  </div>
                  <div>
                    <div className="insight-label">Cycles</div>
                    <div className="insight-value">{analysis.graph_insights.cycles.length}</div>
                  </div>
                  <div>
                    <div className="insight-label">Components</div>
                    <div className="insight-value">{analysis.graph_insights.connected_components.length}</div>
                  </div>
                  <div>
                    <div className="insight-label">Edges</div>
                    <div className="insight-value">{analysis.edges.length}</div>
                  </div>
                </div>

                <h3>Top complex files</h3>
                <div className="pill-list">
                  {analysis.stats.top_complex_files.slice(0, 5).map((item) => (
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
                        {deps.length > 0 ? deps.join(", ") : "No direct dependencies detected"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="panel raw-panel">
              <h2>Repository hash</h2>
              <code>{analysis.repo_hash}</code>
            </section>
          </>
        )}
      </div>
    </div>
  );
}

export default App;