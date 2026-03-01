export type EventType =
  | 'pipeline_status'
  | 'task_created'
  | 'task_assigned'
  | 'task_updated'
  | 'agent_thinking'
  | 'agent_output'
  | 'code_generated'
  | 'review_result'
  | 'test_result'
  | 'error'
  | 'log'

interface BaseEvent {
  run_id: string
  timestamp: string
}

export interface PipelineStatusEvent extends BaseEvent {
  type: 'pipeline_status'
  data: { status: string }
}

export interface TaskCreatedEvent extends BaseEvent {
  type: 'task_created'
  data: { task_id: string; title: string; specialty_tags: string[] }
}

export interface TaskAssignedEvent extends BaseEvent {
  type: 'task_assigned'
  data: { task_id: string; developer: string; developer_emoji: string }
}

export interface TaskUpdatedEvent extends BaseEvent {
  type: 'task_updated'
  data: { task_id: string; status: string }
}

export interface AgentThinkingEvent extends BaseEvent {
  type: 'agent_thinking'
  data: { agent: string; message: string }
}

export interface AgentOutputEvent extends BaseEvent {
  type: 'agent_output'
  data: { agent: string; output: string }
}

export interface CodeGeneratedEvent extends BaseEvent {
  type: 'code_generated'
  data: { agent: string; files: string[] }
}

export interface ReviewResultEvent extends BaseEvent {
  type: 'review_result'
  data: { approved: boolean; comments_count: number }
}

export interface TestResultEvent extends BaseEvent {
  type: 'test_result'
  data: { passed: boolean; test_count: number }
}

export interface ErrorEvent extends BaseEvent {
  type: 'error'
  data: { message: string }
}

export interface LogEvent extends BaseEvent {
  type: 'log'
  data: { message: string }
}

export type PipelineEvent =
  | PipelineStatusEvent
  | TaskCreatedEvent
  | TaskAssignedEvent
  | TaskUpdatedEvent
  | AgentThinkingEvent
  | AgentOutputEvent
  | CodeGeneratedEvent
  | ReviewResultEvent
  | TestResultEvent
  | ErrorEvent
  | LogEvent
