import { FormEvent, useEffect, useMemo, useState } from "react";
import { getRepositoryChat } from "./api/backend";
import { getRepositoryAI } from "./api/backend";
import type { RepositoryAIResponse } from "./types/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  analyzeRepository,
  getArchitectureSummary,
  getFileSummary,
  getHealth,
} from "./api/backend";
import type {
  AnalysisResponse,
  ArchitectureSummaryResponse,
  FileSummaryResponse,
  HealthResponse,
} from "./types/api";
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

function toReactFlowNodes(
  analysis: AnalysisResponse,
  selectedFilePath: string | null
) {
  const groupCounters: Record<string, number> = {};

  const getGroup = (idLower: string) => {
    if (idLower.includes("/api/")) return "api";
    if (idLower.includes("/services/")) return "services";
    if (idLower.includes("/models/")) return "models";
    if (idLower.includes("/core/")) return "core";
    if (idLower.includes("/utils/")) return "utils";
    if (idLower.includes("/parsers/")) return "parsers";
    if (idLower.includes("/tests/")) return "tests";
    return "other";
  };

  const groupOrder = [
    "api",
    "services",
    "models",
    "core",
    "utils",
    "parsers",
    "other",
  ];

  return analysis.nodes.map((node) => {
    const id = String(node.id);

    const label =
      typeof node.label === "string"
        ? node.label
        : String(node.id ?? "file");

    const language =
      typeof (node as any).language === "string"
        ? String((node as any).language)
        : "unknown";
        const complexity =
  typeof (node as any).complexity === "number"
    ? (node as any).complexity
    : 0;

    const isSelected = selectedFilePath === id;

    const idLower = id.toLowerCase();

    let bg = "#1e293b";

    if (idLower.includes("/api/")) {
      bg = "#2563eb";
    } else if (idLower.includes("/services/")) {
      bg = "#16a34a";
    } else if (idLower.includes("/models/")) {
      bg = "#ea580c";
    } else if (idLower.includes("/core/")) {
      bg = "#dc2626";
    } else if (idLower.includes("/utils/")) {
      bg = "#9333ea";
    } else if (idLower.includes("/parsers/")) {
      bg = "#0891b2";
    }

    const group = getGroup(idLower);
    

    const groupIndex = groupOrder.indexOf(group);

    const row = groupCounters[group] ?? 0;

    groupCounters[group] = row + 1;

    const laneX = groupIndex * 420;

    return {
      id,

      data: {
        label: `${label}`,
      },

      position: {
        x: laneX,
        y: row * 140,
      },

    
  style: {
  background: bg,
  color: "#fff",

  border: isSelected
  ? "4px solid #facc15"
  : complexity >= 20
  ? "4px solid #ef4444"
  : complexity >= 12
  ? "4px solid #f97316"
  : complexity >= 6
  ? "4px solid #eab308"
  : "4px solid #22c55e",
  borderRadius: 12,

  padding: 10,

  width: 170,

  fontSize: 12,

  boxShadow: isSelected
    ? "0 0 30px rgba(250,204,21,0.9)"
    : "0 4px 12px rgba(0,0,0,0.2)",
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
}));
}
function healthEmoji(value: string) {
  const v = value.toLowerCase();

  if (v.includes("excellent") || v.includes("high") || v.includes("low")) {
    return "🟢";
  }

  if (v.includes("good") || v.includes("moderate") || v.includes("medium") || v.includes("fair")) {
    return "🟡";
  }

  return "🔴";
}
type ChatTurn = {
  question: string;
  answer: string;
};
function App() {
  const [repoPath, setRepoPath] = useState(DEFAULT_REPO_PATH);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileSummary, setFileSummary] = useState<FileSummaryResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [error, setError] = useState<string>("");
  const [summaryError, setSummaryError] = useState<string>("");
  const [architectureSummary, setArchitectureSummary] =
  useState<ArchitectureSummaryResponse | null>(null);

const [loadingArchitecture, setLoadingArchitecture] = useState(false);

const [architectureError, setArchitectureError] = useState("");
const [searchQuery, setSearchQuery] = useState("");
const [activeGroup, setActiveGroup] = useState("all");
const [repositoryAI, setRepositoryAI] = useState<RepositoryAIResponse | null>(null);
const [loadingRepositoryAI, setLoadingRepositoryAI] = useState(false);
const [repositoryAIError, setRepositoryAIError] = useState("");
const [chatQuestion, setChatQuestion] = useState("");
const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
const [chatLoading, setChatLoading] = useState(false);
const [chatError, setChatError] = useState("");

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

  const graphAnalysis = useMemo(() => {
  if (!analysis) return null;

  const q = searchQuery.trim().toLowerCase();
  const hiddenFiles = new Set([".env", "README.md", "requirements.txt"]);

  const matchesQuery = (file: AnalysisResponse["files"][number]) => {
    if (!q) return true;

    const haystack = [file.id, file.name, file.path, file.language]
      .join(" ")
      .toLowerCase();

    return q
      .split(/\s+/)
      .filter(Boolean)
      .every((token) => haystack.includes(token));
  };

  const matchingIds = new Set(
    analysis.files.filter(matchesQuery).map((file) => file.id)
  );

  const getGroup = (idLower: string) => {
  if (idLower.includes("/api/")) return "api";
  if (idLower.includes("/services/")) return "services";
  if (idLower.includes("/models/")) return "models";
  if (idLower.includes("/core/")) return "core";
  if (idLower.includes("/utils/")) return "utils";
  if (idLower.includes("/parsers/")) return "parsers";
  if (idLower.includes("/tests/")) return "tests";
  return "other";
};

const visibleNodes = analysis.nodes.filter((node) => {
  const id = String(node.id).toLowerCase();
  const group = getGroup(id);

  const baseVisible =
    !hiddenFiles.has(id) &&
    !id.endsWith("__init__.py") &&
    !id.includes("test_") &&
    !id.includes("/tests/");

  if (!baseVisible) return false;

  if (activeGroup !== "all" && group !== activeGroup) return false;

  if (!q) return true;

  return matchingIds.has(String(node.id));
});

  const visibleNodeIds = new Set(
    visibleNodes.map((node) => String(node.id))
  );

  const visibleEdges = analysis.edges.filter(
    (edge) =>
      visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
  );

  const visibleDependencyMap: Record<string, string[]> = {};

  for (const [file, deps] of Object.entries(analysis.dependency_map)) {
    if (!visibleNodeIds.has(file)) continue;

    visibleDependencyMap[file] = deps.filter((dep) =>
      visibleNodeIds.has(dep)
    );
  }

  return {
    ...analysis,
    nodes: visibleNodes,
    edges: visibleEdges,
    dependency_map: visibleDependencyMap,
  };
}, [analysis, searchQuery, activeGroup]);
const filteredAnalysis = graphAnalysis;

const reactFlowEdges = useMemo(() => {
  if (!graphAnalysis) return [];
  return toReactFlowEdges(graphAnalysis);
}, [graphAnalysis]);

const reactFlowNodes = useMemo(() => {
  if (!graphAnalysis) return [];
  const nodes = toReactFlowNodes(graphAnalysis, selectedFilePath);
  return layoutGraph(nodes, reactFlowEdges, "LR").nodes;
}, [graphAnalysis, selectedFilePath, reactFlowEdges]);

const topDependencies = useMemo(() => {
  if (!graphAnalysis) return [];
  return Object.entries(graphAnalysis.dependency_map)
    .slice(0, 8)
    .map(([file, deps]) => ({
      file,
      deps: deps.slice(0, 4),
    }));
}, [graphAnalysis]);

const selectedFileMeta = useMemo(() => {
  if (!graphAnalysis || !selectedFilePath) return null;
  return (
    graphAnalysis.files.find(
      (file) => file.path === selectedFilePath || file.id === selectedFilePath
    ) ?? null
  );
}, [graphAnalysis, selectedFilePath]);
const suggestedChatQuestions = [
  "Where should I start reading this repository?",
  "Explain the architecture.",
  "Which files are the most important?",
  "Which file is the most complex?",
  "What should I refactor first?",
  "How does dependency resolution work?",
];

  
  const handleAnalyze = async (event: FormEvent) => {
  event.preventDefault();

  setError("");
  setSummaryError("");
  setArchitectureError("");
  setRepositoryAIError("");
  setChatTurns([]);
setChatError("");

  setLoadingAnalysis(true);
  setLoadingArchitecture(true);
  setLoadingRepositoryAI(true);

  setAnalysis(null);
  setArchitectureSummary(null);
  setRepositoryAI(null);

  setSelectedFilePath(null);
  setFileSummary(null);

  try {
    const result = await analyzeRepository(repoPath);
    setAnalysis(result);
  } catch (err: any) {
    setError(err?.response?.data?.detail || err?.message || "Analysis failed.");
  } finally {
    setLoadingAnalysis(false);
  }

  try {
    const architecture = await getArchitectureSummary(repoPath);
    setArchitectureSummary(architecture);
  } catch (err: any) {
    setArchitectureError(
      err?.response?.data?.detail ||
        err?.message ||
        "Failed to load architecture summary."
    );
  } finally {
    setLoadingArchitecture(false);
  }

  try {
    const ai = await getRepositoryAI(repoPath);
    setRepositoryAI(ai);
  } catch (err: any) {
    setRepositoryAIError(
      err?.response?.data?.detail ||
        err?.message ||
        "Failed to load repository intelligence."
    );
  } finally {
    setLoadingRepositoryAI(false);
  }
};
const handleRepositoryChat = async (question: string) => {
  const finalQuestion = question.trim();
  if (!finalQuestion) return;

  setChatLoading(true);
  setChatError("");

  try {
    const result = await getRepositoryChat(repoPath, finalQuestion);

    setChatTurns((prev) => [
      { question: finalQuestion, answer: result.answer },
      ...prev,
    ]);

    setChatQuestion("");
  } catch (err: any) {
    setChatError(
      err?.response?.data?.detail ||
        err?.message ||
        "Failed to get repository answer."
    );
  } finally {
    setChatLoading(false);
  }
};
  const handleNodeClick = async (_event: any, node: any) => {
  const filePath = String(node.id);

  

  setSelectedFilePath(filePath);
  setLoadingSummary(true);
  setSummaryError("");
  setFileSummary(null);

  try {
    const summary = await getFileSummary(repoPath, filePath);
    
    setFileSummary(summary);
  } catch (err: any) {
    console.error("SUMMARY ERROR:", err);
    setSummaryError(
      err?.response?.data?.detail ||
        err?.message ||
        "Failed to load file summary."
    );
  } finally {
    setLoadingSummary(false);
  }
};
const clearSelection = () => {
  setSelectedFilePath(null);
  setFileSummary(null);
  setSummaryError("");
};
const resetView = () => {
  setSearchQuery("");
  setActiveGroup("all");

  setSelectedFilePath(null);

  setFileSummary(null);

  setSummaryError("");
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
              <StatCard
                label="Files"
                value={filteredAnalysis.stats.total_files}
                sublabel="scanned"
              />
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
            {loadingArchitecture || architectureSummary || architectureError ? (
  <section className="architecture-panel">
    <div className="architecture-header">
      <div>
        <h2>Architecture summary</h2>
        <p>AI-generated overview of the repository structure.</p>
      </div>

      {architectureSummary ? (
        <div className={`summary-badge ${architectureSummary.cached ? "cached" : "fresh"}`}>
          {architectureSummary.cached ? "Cached" : "Fresh"}
        </div>
      ) : loadingArchitecture ? (
        <div className="summary-badge idle">Loading</div>
      ) : (
        <div className="summary-badge idle">Idle</div>
      )}
    </div>

    {architectureError ? <p className="error">{architectureError}</p> : null}

    {loadingArchitecture && !architectureSummary ? (
      <p className="muted">Generating architecture summary...</p>
    ) : null}

    {architectureSummary ? (
      <>
                <article className="architecture-overview">
  <ReactMarkdown remarkPlugins={[remarkGfm]}>
    {architectureSummary.overview}
  </ReactMarkdown>
</article>
        <div className="architecture-grid">
          <div className="architecture-block">
            <h3>Main modules</h3>
            <div className="pill-list">
              {architectureSummary.main_modules.map((item) => (
                <span className="pill" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="architecture-block">
            <h3>Hotspots</h3>
            <div className="pill-list">
              {architectureSummary.hotspots.map((item) => (
                <span className="pill" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="architecture-block architecture-suggestions">
            <h3>Refactoring suggestions</h3>
            <ol className="suggestion-list">
              {architectureSummary.refactoring_suggestions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          </div>
        </div>

        <div className="architecture-footer">
          <div>
            <span className="architecture-footer-label">Files:</span>{" "}
            {architectureSummary.total_files}
          </div>
          <div>
            <span className="architecture-footer-label">Repo hash:</span>{" "}
            {architectureSummary.repo_hash}
          </div>
        </div>
      </>
    ) : null}
  </section>
) : null}
{loadingRepositoryAI || repositoryAI || repositoryAIError ? (
  <section className="repository-ai-panel">
    <div className="repository-ai-header">
      <div>
        <h2>Repository Intelligence</h2>
        <p>AI-generated health score, recommendations, and hotspots.</p>
      </div>

      {repositoryAI ? (
        <div className="summary-badge fresh">Fresh</div>
      ) : loadingRepositoryAI ? (
        <div className="summary-badge idle">Loading</div>
      ) : (
        <div className="summary-badge idle">Idle</div>
      )}
    </div>

    {repositoryAIError ? <p className="error">{repositoryAIError}</p> : null}

    {loadingRepositoryAI && !repositoryAI ? (
      <p className="muted">Generating repository intelligence...</p>
    ) : null}

    {repositoryAI ? (
      <>
       <div className="repo-ai-score-label">
    ❤️ HEALTH SCORE
</div>

<div className="repo-ai-score-value">
    {repositoryAI.health.score}
</div>

<div className="repo-ai-score-status">
    {repositoryAI.health.score >= 90
        ? "Excellent"
        : repositoryAI.health.score >= 75
        ? "Good"
        : repositoryAI.health.score >= 60
        ? "Fair"
        : "Needs Improvement"}
</div>

          <div className="repo-ai-metric-card">
  <div className="repo-ai-metric-label">🛠 Maintainability</div>
  <div className="repo-ai-metric-value">
    {healthEmoji(repositoryAI.health.maintainability)}{" "}
    {repositoryAI.health.maintainability}
  </div>
</div>

<div className="repo-ai-metric-card">
  <div className="repo-ai-metric-label">🏛 Architecture</div>
  <div className="repo-ai-metric-value">
    {healthEmoji(repositoryAI.health.architecture)}{" "}
    {repositoryAI.health.architecture}
  </div>
</div>

<div className="repo-ai-metric-card">
  <div className="repo-ai-metric-label">⚡ Complexity</div>
  <div className="repo-ai-metric-value">
    {healthEmoji(repositoryAI.health.complexity)}{" "}
    {repositoryAI.health.complexity}
  </div>
</div>

        <article className="repo-ai-summary">
          {repositoryAI.health.summary}
        </article>

        <div className="repo-ai-columns">
          <div className="repo-ai-box">
            <h3>Recommendations</h3>
            <div className="repo-ai-list">
              {repositoryAI.recommendations.map((item) => (
                <div className="repo-ai-item" key={item.title + item.description}>
                  <div className="repo-ai-item-title">{item.title}</div>
                  <div className="repo-ai-item-text">{item.description}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="repo-ai-box">
            <h3>Hotspots</h3>
            <div className="repo-ai-list">
              {repositoryAI.hotspots.map((item) => (
                <div className="repo-ai-item" key={item.file + item.reason}>
                  <div className="repo-ai-item-title">
                    {item.file} <span className="repo-ai-severity">{item.severity}</span>
                  </div>
                  <div className="repo-ai-item-text">{item.reason}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </>
    ) : null}
  </section>
) : null}
<section className="repository-chat-panel">
  <div className="repository-chat-header">
    <div>
      <h2>Ask AI About This Repository</h2>
      <p>
        Ask about architecture, dependencies, hotspots, or where to start
        reading.
      </p>
    </div>
  </div>

  <div className="chat-chip-row">
    {suggestedChatQuestions.map((item) => (
      <button
        key={item}
        type="button"
        className="chat-chip"
        onClick={() => handleRepositoryChat(item)}
      >
        {item}
      </button>
    ))}
  </div>

  <form
    className="chat-form"
    onSubmit={(e) => {
      e.preventDefault();
      handleRepositoryChat(chatQuestion);
    }}
  >
    <input
      value={chatQuestion}
      onChange={(e) => setChatQuestion(e.target.value)}
      placeholder="Ask anything about this repository..."
    />
    <button type="submit" disabled={chatLoading || !chatQuestion.trim()}>
      {chatLoading ? "Thinking..." : "Ask"}
    </button>
  </form>

  {chatError ? <p className="error">{chatError}</p> : null}

  <div className="chat-history">
    {chatTurns.length === 0 ? (
      <p className="muted">
        Try asking where to start, which file is most important, or what should
        be refactored first.
      </p>
    ) : (
      chatTurns.map((turn, index) => (
        <div className="chat-turn" key={`${turn.question}-${index}`}>
          <div className="chat-question">Q: {turn.question}</div>
          <article className="chat-answer">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {turn.answer}
            </ReactMarkdown>
          </article>
        </div>
      ))
    )}
  </div>
</section>
<section className="search-panel">
  <div className="group-filters">
  {[
    "all",
    "api",
    "services",
    "models",
    "core",
    "utils",
    "parsers",
  ].map((group) => (
    <button
      key={group}
      type="button"
      className={
        activeGroup === group
          ? "group-filter active"
          : "group-filter"
      }
      onClick={() => setActiveGroup(group)}
    >
      {group.toUpperCase()}
    </button>
  ))}

  <button
    type="button"
    className="reset-button"
    onClick={resetView}
  >
    RESET VIEW
  </button>
</div>
  <div className="search-panel-header">
    <div>
      <h2>Search files</h2>
      <p>Filter the graph by file name, path, or language.</p>
    </div>

    {searchQuery ? (
      <button
        type="button"
        className="secondary-button"
        onClick={() => setSearchQuery("")}
      >
        Clear
      </button>
    ) : null}
  </div>

  <div className="search-row">
    <input
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      placeholder="Try: scanner, services, python..."
    />
  </div>

    {graphAnalysis ? (
  <div className="search-status">
    <span>📁 {graphAnalysis.nodes.length} files visible</span>

    {activeGroup !== "all" && (
      <span>🏷️ {activeGroup.toUpperCase()}</span>
    )}

    {searchQuery && (
      <span>🔍 "{searchQuery}"</span>
    )}
  </div>
) : null}
  
</section>
            {graphAnalysis ? (
  reactFlowNodes.length === 0 ? (
    <div className="empty-state">
      <div className="empty-icon">🔍</div>

      <h3>No files matched your search</h3>

      <p>
        Try another search term or click
        <strong> Reset View </strong>
        to clear all filters.
      </p>

      <div className="empty-examples">
        <span>scanner</span>
        <span>services</span>
        <span>graph</span>
        <span>python</span>
      </div>
    </div>
  ) : (
    <GraphCanvas
      nodes={reactFlowNodes}
      edges={reactFlowEdges}
      onNodeClick={handleNodeClick}
      onPaneClick={clearSelection}
    />
  )
) : null}

            <section className="summary-panel">
              <div className="summary-header">
                <div>
                  <h2>File summary</h2>
                  <p>Click a node in the graph to load its AI summary and file metadata.</p>
                </div>

                {fileSummary ? (
                  <div className={`summary-badge ${fileSummary.cached ? "cached" : "fresh"}`}>
                    {fileSummary.cached ? "Cached" : "Fresh"}
                  </div>
                ) : (
                  <div className="summary-badge idle">Idle</div>
                )}
              </div>
              {selectedFilePath ? (
  <div className="selected-file-chip">
    Selected: {selectedFilePath}
  </div>
) : null}

              {!selectedFilePath ? (
                <div className="summary-empty">
                  Click any visible node to inspect its AI explanation.
                </div>
              ) : (
                <>
                  {selectedFileMeta ? (
                    <div className="summary-meta-grid">
                      <div className="summary-meta">
                        <div className="summary-meta-label">File</div>
                        <div className="summary-meta-value">{selectedFileMeta.path}</div>
                      </div>
                      <div className="summary-meta">
                        <div className="summary-meta-label">Language</div>
                        <div className="summary-meta-value">{selectedFileMeta.language}</div>
                      </div>
                      <div className="summary-meta">
                        <div className="summary-meta-label">Size</div>
                        <div className="summary-meta-value">{selectedFileMeta.size} bytes</div>
                      </div>
                      <div className="summary-meta">
                        <div className="summary-meta-label">Hash</div>
                        <div className="summary-meta-value summary-hash">
                          {selectedFileMeta.file_hash}
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {loadingSummary ? <p className="muted">Loading summary...</p> : null}
                  {summaryError ? <p className="error">{summaryError}</p> : null}

                                    {fileSummary ? (
  <article className="summary-text">
    <ReactMarkdown>
      {fileSummary.summary}
    </ReactMarkdown>
  </article>
) : null}
                </>
              )}
            </section>

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