import { useMemo, useState } from 'react'
import { usePipeline } from '@/contexts/PipelineContext'
import type { DeveloperConfig } from '@/types'
import type { PipelineEvent } from '@/types/events'

interface DeveloperDetailModalProps {
  dev: DeveloperConfig
  onClose: () => void
}

type FilterType = 'all' | 'thinking' | 'output' | 'code'

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString('en-US', { hour12: false })
  } catch {
    return ''
  }
}

export function DeveloperDetailModal({ dev, onClose }: DeveloperDetailModalProps) {
  const { events, tasks } = usePipeline()
  const [filter, setFilter] = useState<FilterType>('all')
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null)

  // Get events related to this developer
  const devEvents = useMemo(() => {
    return events.filter((e) => {
      if (e.type === 'agent_thinking' || e.type === 'agent_output' || e.type === 'code_generated') {
        return e.data.agent === dev.name
      }
      if (e.type === 'task_assigned') {
        return e.data.developer === dev.name
      }
      return false
    })
  }, [events, dev.name])

  const filteredEvents = useMemo(() => {
    if (filter === 'all') return devEvents
    if (filter === 'thinking') return devEvents.filter((e) => e.type === 'agent_thinking')
    if (filter === 'output') return devEvents.filter((e) => e.type === 'agent_output')
    if (filter === 'code') return devEvents.filter((e) => e.type === 'code_generated')
    return devEvents
  }, [devEvents, filter])

  // Tasks assigned to this developer
  const assignedTasks = tasks.filter((t) => t.assigned_to === dev.name)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="detail-modal-header">
          <h2>
            <span style={{ marginRight: '0.5rem' }}>{dev.emoji}</span>
            {dev.name}
          </h2>
          <button className="secondary" onClick={onClose}>Close</button>
        </div>

        <div className="detail-section">
          <div className="detail-row">
            <span className="detail-label">Specialty</span>
            <span>{dev.specialty}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Status</span>
            <span style={{ color: dev.enabled ? 'var(--accent-green)' : 'var(--text-muted)' }}>
              {dev.enabled ? 'Active' : 'Disabled'}
            </span>
          </div>
          {dev.custom_prompt && (
            <div className="detail-row">
              <span className="detail-label">Custom Prompt</span>
              <span className="detail-description">{dev.custom_prompt}</span>
            </div>
          )}
        </div>

        {assignedTasks.length > 0 && (
          <div className="detail-section">
            <h3>Assigned Tasks ({assignedTasks.length})</h3>
            <div className="detail-task-list">
              {assignedTasks.map((task) => (
                <div key={task.id} className="detail-task-item">
                  <span className="detail-task-status" data-status={task.status} />
                  <span>{task.title}</span>
                  <span className="detail-task-status-label">{task.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="detail-section">
          <div className="detail-section-header">
            <h3>Thought Process ({filteredEvents.length} events)</h3>
            <div className="detail-filters">
              {(['all', 'thinking', 'output', 'code'] as FilterType[]).map((f) => (
                <button
                  key={f}
                  className="detail-filter-btn"
                  data-active={filter === f}
                  onClick={() => setFilter(f)}
                >
                  {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="detail-event-list">
            {filteredEvents.length === 0 && (
              <div className="detail-empty">No events yet for {dev.name}.</div>
            )}
            {filteredEvents.map((event, i) => (
              <div
                key={i}
                className="detail-event-row detail-event-expandable"
                onClick={() => setExpandedEvent(expandedEvent === i ? null : i)}
              >
                <span className="detail-event-time">{formatTime(event.timestamp)}</span>
                <span className="detail-event-type">{eventTypeLabel(event)}</span>
                <span className="detail-event-msg">
                  {expandedEvent === i ? eventFull(event) : eventPreview(event)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function eventTypeLabel(event: PipelineEvent): string {
  switch (event.type) {
    case 'agent_thinking': return 'Thinking'
    case 'agent_output': return 'Output'
    case 'code_generated': return 'Code'
    case 'task_assigned': return 'Assigned'
    default: return event.type
  }
}

function eventPreview(event: PipelineEvent): string {
  switch (event.type) {
    case 'agent_thinking': return event.data.message
    case 'agent_output': return event.data.output.slice(0, 150) + (event.data.output.length > 150 ? ' [click to expand]' : '')
    case 'code_generated': return `Generated ${event.data.files.length} files: ${event.data.files.join(', ')}`
    case 'task_assigned': return `Assigned to task`
    default: return ''
  }
}

function eventFull(event: PipelineEvent): string {
  switch (event.type) {
    case 'agent_thinking': return event.data.message
    case 'agent_output': return event.data.output
    case 'code_generated': return `Generated ${event.data.files.length} files: ${event.data.files.join(', ')}`
    case 'task_assigned': return `Assigned to task`
    default: return ''
  }
}
