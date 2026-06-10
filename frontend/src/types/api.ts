export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  debug: boolean;
}

export interface AnalyzeRequest {
  repo_path: string;
  include_ai_summary?: boolean;
}

export interface AnalysisStats {
  total_files: number;
  total_loc: number;
  total_blank_lines: number;
  total_comment_lines: number;
  total_code_lines: number;
  total_complexity: number;
  average_complexity: number;
  top_complex_files: Array<{
    file: string;
    complexity: number;
  }>;
}

export interface GraphInsights {
  isolated_files: string[];
  top_incoming: Array<{ file: string; count: number }>;
  top_outgoing: Array<{ file: string; count: number }>;
  connected_components: string[][];
  cycles: string[][];
}

export interface AnalysisResponse {
  repo_path: string;
  files: Array<{
    id: string;
    name: string;
    path: string;
    language: string;
    size: number;
    file_hash: string;
    is_binary: boolean;
    line_count: number;
    last_modified: string;
    metadata: Record<string, unknown>;
  }>;
  nodes: Array<Record<string, unknown>>;
  edges: Array<{
    source: string;
    target: string;
    relation: string;
    weight: number;
    bidirectional: boolean;
    metadata: Record<string, unknown>;
  }>;
  file_metrics: Record<string, Record<string, unknown>>;
  stats: AnalysisStats;
  graph_insights: GraphInsights;
  repo_hash: string;
  dependency_map: Record<string, string[]>;
}