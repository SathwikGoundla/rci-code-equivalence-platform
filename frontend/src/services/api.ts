import axios from 'axios';
import type {
  HealthResponse,
  SystemStatusResponse,
  SystemInfoResponse,
  AnalysisResult,
  AnalysisSummary,
} from '../types';

// All API calls go to localhost — no external network dependency
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ── Health ────────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health');
  return data;
}

export async function getStatus(): Promise<SystemStatusResponse> {
  const { data } = await api.get<SystemStatusResponse>('/status');
  return data;
}

export async function getSystemInfo(): Promise<SystemInfoResponse> {
  const { data } = await api.get<SystemInfoResponse>('/system-info');
  return data;
}

// ── Analysis ──────────────────────────────────────────────────────────────────

export async function uploadAndAnalyze(
  cFile: File,
  fortranFile: File,
  projectId: string | null = null
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append('c_file', cFile);
  formData.append('fortran_file', fortranFile);
  if (projectId) {
    formData.append('project_id', projectId);
  }

  const { data } = await api.post<AnalysisResult>('/analysis/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function listAnalyses(projectId: string | null = null): Promise<AnalysisSummary[]> {
  const { data } = await api.get<AnalysisSummary[]>('/analysis/', {
    params: projectId ? { project_id: projectId } : {},
  });
  return data;
}

export async function getAnalysis(sessionId: string): Promise<AnalysisResult> {
  const { data } = await api.get<AnalysisResult>(`/analysis/${sessionId}`);
  return data;
}

// ── Projects ──────────────────────────────────────────────────────────────────

export async function listProjects() {
  const { data } = await api.get('/projects/');
  return data;
}

export async function createProject(name: string, description: string = '') {
  const { data } = await api.post('/projects/', { name, description });
  return data;
}

export { api };

