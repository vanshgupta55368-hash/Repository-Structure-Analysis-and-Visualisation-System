import api from "./client";
import type { AnalysisResponse, HealthResponse } from "../types/api";

export async function getHealth(): Promise<HealthResponse> {
  const response = await api.get("/health");
  return response.data;
}

export async function analyzeRepository(repoPath: string): Promise<AnalysisResponse> {
  const response = await api.post("/analyze", {
    repo_path: repoPath,
    include_ai_summary: false,
  });
  return response.data;
}