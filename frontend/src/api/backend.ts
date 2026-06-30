import api from "./client";
import type { RepositoryChatResponse } from "../types/api";
import type {
  AnalysisResponse,
  ArchitectureSummaryResponse,
  FileSummaryResponse,
  HealthResponse,
} from "../types/api";

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

export async function getFileSummary(
  repoPath: string,
  filePath: string
): Promise<FileSummaryResponse> {
  const response = await api.post("/summary/file", {
    repo_path: repoPath,
    file_path: filePath,
  });
  return response.data;
}

export async function getArchitectureSummary(
  repoPath: string
): Promise<ArchitectureSummaryResponse> {
  const response = await api.post("/summary/architecture", {
    repo_path: repoPath,
  });
  return response.data;
}
import type { RepositoryAIResponse } from "../types/api";

export async function getRepositoryAI(repoPath: string): Promise<RepositoryAIResponse> {
  const response = await api.post("/repository-ai", {
    repo_path: repoPath,
  });
  return response.data;
}
export async function getRepositoryChat(
  repoPath: string,
  question: string
): Promise<RepositoryChatResponse> {
  const response = await api.post("/repository-chat", {
    repo_path: repoPath,
    question,
  });

  return response.data;
}