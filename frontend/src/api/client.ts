import type {
  AnalyzeResponse,
  Bbox,
  BuildingFeature,
  BuildingFeatureCollection,
  FranceRankAreasResponse,
  Project,
  ProjectCreateInput,
  ProjectSummary
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ?? response.statusText;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail);
  }

  return response.json() as Promise<T>;
}

export function getDemoProject(): Promise<Project> {
  return request<Project>("/api/projects/demo");
}

export function createProject(payload: ProjectCreateInput): Promise<Project> {
  return request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function analyzeProject(projectId: string, bbox: Bbox, limit = 220): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>(`/api/projects/${projectId}/analyze-bbox`, {
    method: "POST",
    body: JSON.stringify({ bbox, limit })
  });
}

export function getProjectBuildings(projectId: string): Promise<BuildingFeatureCollection> {
  return request<BuildingFeatureCollection>(`/api/projects/${projectId}/buildings`);
}

export function getProjectSummary(projectId: string): Promise<ProjectSummary> {
  return request<ProjectSummary>(`/api/projects/${projectId}/summary`);
}

export function getBuilding(buildingId: string): Promise<BuildingFeature> {
  return request<BuildingFeature>(`/api/buildings/${buildingId}`);
}

export function rankFranceAreas(limit = 12): Promise<FranceRankAreasResponse> {
  return request<FranceRankAreasResponse>("/api/france/rank-areas", {
    method: "POST",
    body: JSON.stringify({ limit, include_weather: true, include_pvgis: true })
  });
}
