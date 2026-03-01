import { usePipeline } from '@/contexts/PipelineContext'
import type { PipelineTask } from '@/types'
import type { PipelineEvent } from '@/types/events'

interface TaskDetailModalProps {
  task: PipelineTask
  onClose: () => void
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'Pending', color: 'var(--text-muted)' },
  assigned: { label: 'Assigned', color: 'var(--accent-blue)' },
  in_progress: { label: 'In Progress', color: 'var(--accent-yellow)' },
  in_review: { label: 'In Review', color: 'var(--accent-purple)' },
  review_rejected: { label: 'Review Rejected', color: 'var(--accent-red)' },
  testing: { label: 'Testing', color: 'var(--accent-yellow)' },
  completed: { label: 'Completed', color: 'var(--accent-green)' },
  failed: { label: 'Failed', color: 'var(--accent-red)' },
}

function isTaskEvent(event: PipelineEvent, taskId: string): boolean {
  if (event.type === 'task_created' || event.type === 'task_assigned' || event.type === 'task_updated') {
    return event.data.task_id === taskId
  }
  return false
}

function isDeveloperEvent(event: PipelineEvent, devName: string | null): boolean {
  if (!devName) return false
  if (event.type === 'agent_thinking' || event.type === 'agent_output' || event.type === 'code_generated') {
    return event.data.agent === devName
  }
  return false
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString('en-US', { hour12: false })
  } catch {
    return ''
  }
}

export function TaskDetailModal({ task, onClose }: TaskDetailModalProps) {
  const { events } = usePipeline()

  // Get events related to this task (direct task events + developer events)
  const relatedEvents = events.filter(
    (e) => isTaskEvent(e, task.id) || isDeveloperEvent(e, task.assigned_to),
  )

  const statusInfo = STATUS_LABELS[task.status] || { label: task.status, color: 'var(--text-muted)' }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="detail-modal-header">
          <h2>{task.title}</h2>
          <button className="secondary" onClick={onClose}>Close</button>
        </div>

        <div className="detail-section">
          <div className="detail-row">
            <span className="detail-label">Status</span>
            <span className="detail-status-badge" style={{ background: statusInfo.color }}>
              {statusInfo.label}
            </span>
          </div>
          {task.assigned_to && (
            <div className="detail-row">
              <span className="detail-label">Assigned To</span>
              <span>{task.assigned_to}</span>
            </div>
          )}
          {task.specialty_tags && task.specialty_tags.length > 0 && (
            <div className="detail-row">
              <span className="detail-label">Tags</span>
              <div className="detail-tags">
                {task.specialty_tags.map((tag) => (
                  <span key={tag} className="task-card-tag">{tag}</span>
                ))}
              </div>
            </div>
          )}
          {task.description && (
            <div className="detail-row">
              <span className="detail-label">Description</span>
              <span className="detail-description">{task.description}</span>
            </div>
          )}
        </div>

        {task.review_notes && (
          <div className="detail-section">
            <h3>Review Notes</h3>
            <pre className="detail-pre">{task.review_notes}</pre>
          </div>
        )}

        {task.test_results && (
          <div className="detail-section">
            <h3>Test Results</h3>
            <pre className="detail-pre">{task.test_results}</pre>
          </div>
        )}

        <div className="detail-section">
          <h3>Activity ({relatedEvents.length} events)</h3>
          <div className="detail-event-list">
            {relatedEvents.length === 0 && (
              <div className="detail-empty">No events yet for this task.</div>
            )}
            {relatedEvents.map((event, i) => (
              <div key={i} className="detail-event-row">
                <span className="detail-event-time">{formatTime(event.timestamp)}</span>
                <span className="detail-event-type">{event.type}</span>
                <span className="detail-event-msg">{eventSummary(event)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function eventSummary(event: PipelineEvent): string {
  switch (event.type) {
    case 'task_created': return `Task created`
    case 'task_assigned': return `Assigned to ${event.data.developer}`
    case 'task_updated': return `Status changed to ${event.data.status}`
    case 'agent_thinking': return event.data.message
    case 'agent_output': return event.data.output.slice(0, 200) + (event.data.output.length > 200 ? '...' : '')
    case 'code_generated': return `Generated ${event.data.files.length} files: ${event.data.files.join(', ')}`
    case 'review_result': return `Review: ${event.data.approved ? 'Approved' : 'Rejected'}`
    case 'test_result': return `Tests: ${event.data.passed ? 'Passed' : 'Failed'} (${event.data.test_count})`
    default: return ''
  }
}
