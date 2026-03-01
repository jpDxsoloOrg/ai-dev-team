import { useState } from 'react'
import type { PipelineTask } from '@/types'

interface TaskCardProps {
  task: PipelineTask
}

export function TaskCard({ task }: TaskCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="task-card" onClick={() => setExpanded(!expanded)}>
      <div className="task-card-title">{task.title}</div>
      <div className="task-card-meta">
        {task.assigned_to && <span>{task.assigned_to}</span>}
        {task.specialty_tags?.map((tag) => (
          <span key={tag} className="task-card-tag">{tag}</span>
        ))}
      </div>
      {expanded && (task.code_output || task.review_notes || task.test_results) && (
        <div className="task-card-details">
          {task.review_notes && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Review: {task.review_notes}
            </div>
          )}
          {task.test_results && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Tests: {task.test_results}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
