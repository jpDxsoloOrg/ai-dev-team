import { usePipeline } from '@/contexts/PipelineContext'
import type { PipelineTask, TaskStatus } from '@/types'
import { TaskCard } from './TaskCard'

interface Column {
  key: string
  label: string
  statuses: TaskStatus[]
}

const COLUMNS: Column[] = [
  { key: 'pending', label: 'Pending', statuses: ['pending'] },
  { key: 'active', label: 'In Progress', statuses: ['assigned', 'in_progress'] },
  { key: 'review', label: 'In Review', statuses: ['in_review', 'review_rejected'] },
  { key: 'done', label: 'Completed', statuses: ['completed'] },
  { key: 'failed', label: 'Failed', statuses: ['failed'] },
]

export function TaskBoard() {
  const { tasks } = usePipeline()

  function tasksForColumn(col: Column): PipelineTask[] {
    return tasks.filter((t) => col.statuses.includes(t.status))
  }

  if (tasks.length === 0) {
    return <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No tasks yet. Start a pipeline to see tasks appear here.</div>
  }

  return (
    <div className="task-board">
      {COLUMNS.map((col) => {
        const colTasks = tasksForColumn(col)
        return (
          <div key={col.key} className="task-column">
            <div className="task-column-header">
              <span>{col.label}</span>
              <span className="task-column-count">{colTasks.length}</span>
            </div>
            {colTasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        )
      })}
    </div>
  )
}
