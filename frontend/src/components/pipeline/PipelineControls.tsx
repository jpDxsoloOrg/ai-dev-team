import { useState } from 'react'
import { usePipeline } from '@/contexts/PipelineContext'
import { useSettings } from '@/contexts/SettingsContext'

export function PipelineControls() {
  const { status, start, pause, resume, stop } = usePipeline()
  const { selectedProvider, selectedModel } = useSettings()
  const [goal, setGoal] = useState('')

  const isRunning = status !== null && status !== 'completed' && status !== 'failed' && status !== 'cancelled'
  const isPaused = status === 'paused'

  async function handleStart() {
    if (!goal.trim() || !selectedProvider || !selectedModel) return
    await start(goal, selectedProvider, selectedModel)
    setGoal('')
  }

  return (
    <div className="pipeline-controls">
      {!isRunning && (
        <div className="pipeline-goal-form">
          <textarea
            placeholder="Describe what you want to build..."
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.metaKey) handleStart()
            }}
          />
          <button
            className="primary"
            onClick={handleStart}
            disabled={!goal.trim() || !selectedProvider}
          >
            Start
          </button>
        </div>
      )}
      {isRunning && (
        <div className="pipeline-actions">
          {isPaused ? (
            <button className="primary" onClick={resume}>Resume</button>
          ) : (
            <button className="secondary" onClick={pause}>Pause</button>
          )}
          <button className="danger" onClick={stop}>Stop</button>
        </div>
      )}
    </div>
  )
}
