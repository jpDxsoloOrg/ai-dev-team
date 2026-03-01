import { usePipeline } from '@/contexts/PipelineContext'

const STATUS_COLORS: Record<string, string> = {
  pending: 'var(--bg-tertiary)',
  assigned: 'var(--accent-purple)',
  in_progress: 'var(--accent-orange)',
  in_review: 'var(--accent-yellow)',
  review_rejected: 'var(--accent-red)',
  testing: 'var(--accent-blue)',
  completed: 'var(--accent-green)',
  failed: 'var(--accent-red)',
}

export function ProgressBar() {
  const { tasks, status } = usePipeline()

  if (tasks.length === 0) return null

  const completed = tasks.filter((t) => t.status === 'completed').length
  const failed = tasks.filter((t) => t.status === 'failed').length
  const inProgress = tasks.filter(
    (t) => t.status !== 'pending' && t.status !== 'completed' && t.status !== 'failed',
  ).length

  return (
    <div className="progress-bar-container">
      <div className="progress-bar">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="progress-segment"
            style={{
              width: `${100 / tasks.length}%`,
              background: STATUS_COLORS[task.status] || 'var(--bg-tertiary)',
            }}
          />
        ))}
      </div>
      <div className="progress-label">
        {status && <span>{status}</span>}
        {' '}
        {completed}/{tasks.length} done
        {failed > 0 && `, ${failed} failed`}
        {inProgress > 0 && `, ${inProgress} active`}
      </div>
    </div>
  )
}
