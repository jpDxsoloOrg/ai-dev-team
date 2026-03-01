import { useState } from 'react'
import type { PipelineTask, DeveloperConfig } from '@/types'
import { usePipeline } from '@/contexts/PipelineContext'
import { useDevelopers } from '@/hooks/useDevelopers'
import { TaskDetailModal } from './TaskDetailModal'

interface TaskCardProps {
  task: PipelineTask
}

export function TaskCard({ task }: TaskCardProps) {
  const [showDetail, setShowDetail] = useState(false)
  const [selectedDev, setSelectedDev] = useState('')
  const { status: pipelineStatus, assignTask } = usePipeline()
  const { developers } = useDevelopers()

  const canAssign = task.status === 'pending' && pipelineStatus === 'assigning'

  const grouped = (() => {
    const groups: Record<string, DeveloperConfig[]> = {}
    for (const dev of developers.filter((d) => d.enabled)) {
      const key = dev.team || 'Unassigned'
      if (!groups[key]) groups[key] = []
      groups[key].push(dev)
    }
    return groups
  })()

  const sortedTeams = Object.keys(grouped).sort((a, b) => {
    if (a === 'Unassigned') return 1
    if (b === 'Unassigned') return -1
    return a.localeCompare(b)
  })

  async function handleAssign() {
    if (!selectedDev) return
    await assignTask(task.id, selectedDev)
    setSelectedDev('')
  }

  return (
    <>
      <div className="task-card" onClick={() => !canAssign && setShowDetail(true)}>
        <div className="task-card-title">{task.title}</div>
        <div className="task-card-meta">
          {task.assigned_to && <span>{task.assigned_to}</span>}
          {task.specialty_tags?.map((tag) => (
            <span key={tag} className="task-card-tag">{tag}</span>
          ))}
        </div>
        {canAssign && (
          <div
            className="task-assign-row"
            style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}
            onClick={(e) => e.stopPropagation()}
          >
            <select
              value={selectedDev}
              onChange={(e) => setSelectedDev(e.target.value)}
              style={{ flex: 1, fontSize: '0.8rem' }}
            >
              <option value="">Assign to...</option>
              {sortedTeams.map((teamName) => (
                <optgroup key={teamName} label={teamName}>
                  {grouped[teamName].map((dev) => (
                    <option key={dev.id} value={dev.id}>
                      {dev.emoji} {dev.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <button
              className="primary"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
              disabled={!selectedDev}
              onClick={handleAssign}
            >
              Assign
            </button>
          </div>
        )}
      </div>
      {showDetail && (
        <TaskDetailModal task={task} onClose={() => setShowDetail(false)} />
      )}
    </>
  )
}
