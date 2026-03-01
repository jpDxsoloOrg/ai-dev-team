export type PipelineStatus =
  | 'pending'
  | 'planning'
  | 'assigning'
  | 'developing'
  | 'reviewing'
  | 'testing'
  | 'merging'
  | 'completed'
  | 'failed'
  | 'paused'
  | 'cancelled'

export type TaskStatus =
  | 'pending'
  | 'assigned'
  | 'in_progress'
  | 'in_review'
  | 'review_rejected'
  | 'testing'
  | 'completed'
  | 'failed'

export interface DeveloperConfig {
  id: string
  name: string
  emoji: string
  color: string
  specialty: string
  custom_prompt: string
  enabled: boolean
}

export interface PipelineTask {
  id: string
  run_id: string
  title: string
  description: string
  status: TaskStatus
  assigned_to: string | null
  specialty_tags: string[] | null
  code_output: string | null
  review_notes: string | null
  test_results: string | null
  file_paths: string[] | null
  created_at: string
  updated_at: string
}

export interface PipelineRun {
  id: string
  goal: string
  status: PipelineStatus
  provider: string
  model: string
  project_path: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
  error_message: string | null
  total_tasks: number
  completed_tasks: number
  tasks: PipelineTask[]
}

export interface ProviderInfo {
  name: string
  available: boolean
  models: string[]
}

export interface ApiKeyStatus {
  configured: boolean
  masked: string | null
}

export interface PipelineStartRequest {
  goal: string
  provider: string
  model: string
  project_path?: string | null
}
