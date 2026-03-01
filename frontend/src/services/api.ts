import type {
  DeveloperConfig,
  PipelineRun,
  PipelineStartRequest,
  ProviderInfo,
} from '@/types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const pipelineApi = {
  start: (data: PipelineStartRequest) =>
    request<PipelineRun>('/pipeline/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  pause: (runId: string) =>
    request<{ status: string }>(`/pipeline/${runId}/pause`, { method: 'POST' }),
  resume: (runId: string) =>
    request<{ status: string }>(`/pipeline/${runId}/resume`, { method: 'POST' }),
  stop: (runId: string) =>
    request<{ status: string }>(`/pipeline/${runId}/stop`, { method: 'POST' }),
  get: (runId: string) => request<PipelineRun>(`/pipeline/${runId}`),
  assign: (runId: string, taskId: string, devId: string) =>
    request<{ status: string }>(`/pipeline/${runId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, dev_id: devId }),
    }),
  setAutoAssign: (runId: string, enabled: boolean) =>
    request<{ status: string; enabled: boolean }>(`/pipeline/${runId}/auto-assign`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
}

export const developersApi = {
  list: () => request<DeveloperConfig[]>('/developers'),
  create: (data: Partial<DeveloperConfig>) =>
    request<DeveloperConfig>('/developers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<DeveloperConfig>) =>
    request<DeveloperConfig>(`/developers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/developers/${id}`, { method: 'DELETE' }),
  duplicate: (id: string) =>
    request<DeveloperConfig>(`/developers/${id}/duplicate`, { method: 'POST' }),
  toggle: (id: string) =>
    request<DeveloperConfig>(`/developers/${id}/toggle`, { method: 'PATCH' }),
}

export const providersApi = {
  list: () => request<ProviderInfo[]>('/providers'),
  models: (name: string) =>
    request<{ provider: string; models: string[] }>(`/providers/${name}/models`),
}

export const settingsApi = {
  saveKey: (provider: string, api_key: string) =>
    request<{ status: string }>('/settings/api-keys', {
      method: 'PUT',
      body: JSON.stringify({ provider, api_key }),
    }),
  deleteKey: (provider: string) =>
    request<{ status: string }>(`/settings/api-keys/${provider}`, {
      method: 'DELETE',
    }),
  listKeys: () =>
    request<{
      keys: Record<string, { configured: boolean; masked: string | null }>
    }>('/settings/api-keys'),
}

export const historyApi = {
  list: (limit = 20, offset = 0) =>
    request<{ total: number; runs: PipelineRun[] }>(
      `/runs?limit=${limit}&offset=${offset}`,
    ),
  get: (runId: string) => request<PipelineRun>(`/runs/${runId}`),
}

export interface GitHubIssue {
  number: number
  title: string
  body: string
  labels: string[]
}

export const projectsApi = {
  load: (source: string, path: string) =>
    request<{
      path: string
      summary: string
      detected_stack: string[]
      file_count: number
      github_owner?: string
      github_repo?: string
    }>('/projects/load', { method: 'POST', body: JSON.stringify({ source, path }) }),
  getFiles: (path: string) =>
    request<{ files: Record<string, string> }>(
      `/projects/files?path=${encodeURIComponent(path)}`,
    ),
  getWorkspaceFiles: (runId: string) =>
    request<{ files: Record<string, string> }>(
      `/projects/workspace-files/${runId}`,
    ),
  getIssues: (owner: string, repo: string) =>
    request<{ issues: GitHubIssue[] }>(
      `/projects/github-issues?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}`,
    ),
}

export const exportApi = {
  zipUrl: (runId: string) => `${BASE}/export/${runId}/zip`,
  transcriptUrl: (runId: string) => `${BASE}/export/${runId}/transcript`,
  git: (runId: string) =>
    request<{ message: string; sha: string }>(`/export/${runId}/git`, { method: 'POST' }),
}
