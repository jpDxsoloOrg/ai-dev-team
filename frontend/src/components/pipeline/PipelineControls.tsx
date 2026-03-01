import { useState, useEffect, useMemo } from 'react'
import { usePipeline } from '@/contexts/PipelineContext'
import { useSettings } from '@/contexts/SettingsContext'
import { useDevelopers } from '@/hooks/useDevelopers'
import { useRecentItems } from '@/hooks/useRecentItems'
import { projectsApi } from '@/services/api'
import type { GitHubIssue } from '@/services/api'

interface PipelineControlsProps {
  projectPath?: string
  githubOwner?: string
  githubRepo?: string
}

export function PipelineControls({ projectPath, githubOwner, githubRepo }: PipelineControlsProps) {
  const { status, start, pause, resume, stop, setAutoAssign } = usePipeline()
  const { selectedProvider, selectedModel } = useSettings()
  const { developers } = useDevelopers()
  const [goal, setGoal] = useState('')
  const [selectedTeam, setSelectedTeam] = useState('')
  const [autoAssign, setAutoAssignLocal] = useState(true)
  const [issues, setIssues] = useState<GitHubIssue[]>([])
  const [issuesLoading, setIssuesLoading] = useState(false)
  const recentGoals = useRecentItems('ai-dev-team:recent-goals')

  const teams = useMemo(
    () => [...new Set(developers.filter((d) => d.enabled && d.team).map((d) => d.team))].sort(),
    [developers],
  )

  const isRunning = status !== null && status !== 'completed' && status !== 'failed' && status !== 'cancelled'
  const isPaused = status === 'paused'

  // Fetch GitHub issues when owner/repo are available
  useEffect(() => {
    if (!githubOwner || !githubRepo) {
      setIssues([])
      return
    }
    setIssuesLoading(true)
    projectsApi.getIssues(githubOwner, githubRepo)
      .then((data) => setIssues(data.issues))
      .catch(() => setIssues([]))
      .finally(() => setIssuesLoading(false))
  }, [githubOwner, githubRepo])

  async function handleStart() {
    if (!goal.trim() || !selectedProvider || !selectedModel) return
    recentGoals.add(goal.trim())
    await start(goal, selectedProvider, selectedModel, projectPath, selectedTeam || undefined, autoAssign)
    setGoal('')
  }

  async function handleAutoAssignToggle() {
    const next = !autoAssign
    setAutoAssignLocal(next)
    if (isRunning) {
      await setAutoAssign(next)
    }
  }

  function selectIssue(value: string) {
    if (!value) return
    const issue = issues.find((i) => String(i.number) === value)
    if (issue) {
      const body = issue.body ? `\n\n${issue.body}` : ''
      setGoal(`#${issue.number}: ${issue.title}${body}`)
    }
  }

  return (
    <div className="pipeline-controls">
      {!isRunning && (
        <>
          {issues.length > 0 && (
            <select
              className="recent-select"
              value=""
              onChange={(e) => selectIssue(e.target.value)}
            >
              <option value="">{issuesLoading ? 'Loading issues...' : `GitHub Issues (${issues.length})`}</option>
              {issues.map((issue) => (
                <option key={issue.number} value={issue.number}>
                  #{issue.number}: {issue.title.length > 70 ? issue.title.slice(0, 70) + '...' : issue.title}
                </option>
              ))}
            </select>
          )}
          {recentGoals.items.length > 0 && (
            <select
              className="recent-select"
              value=""
              onChange={(e) => { if (e.target.value) setGoal(e.target.value) }}
            >
              <option value="">Recent goals...</option>
              {recentGoals.items.map((item, i) => (
                <option key={i} value={item}>
                  {item.length > 80 ? item.slice(0, 80) + '...' : item}
                </option>
              ))}
            </select>
          )}
          <div className="pipeline-options" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              style={{ flex: 1 }}
            >
              <option value="">All Teams</option>
              {teams.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
              <input
                type="checkbox"
                checked={autoAssign}
                onChange={handleAutoAssignToggle}
              />
              Auto-assign
            </label>
          </div>
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
        </>
      )}
      {isRunning && (
        <div className="pipeline-actions">
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={autoAssign}
              onChange={handleAutoAssignToggle}
            />
            Auto-assign
          </label>
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
