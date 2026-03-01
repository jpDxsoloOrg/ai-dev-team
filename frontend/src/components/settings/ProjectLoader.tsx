import { useState } from 'react'
import { useRecentItems } from '@/hooks/useRecentItems'

type ProjectType = 'new' | 'local' | 'github'

interface ProjectLoaderProps {
  onLoad: (projectPath: string, githubOwner?: string, githubRepo?: string) => void
}

export function ProjectLoader({ onLoad }: ProjectLoaderProps) {
  const [type, setType] = useState<ProjectType>('new')
  const [path, setPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState<string | null>(null)
  const recentProjects = useRecentItems('ai-dev-team:recent-projects')

  async function handleLoad() {
    if (!path.trim()) return
    setLoading(true)
    try {
      const res = await fetch('/api/projects/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: type, path: path.trim() }),
      })
      const data = await res.json()
      if (res.ok) {
        setInfo(`Loaded: ${data.summary || data.path}`)
        recentProjects.add(path.trim())
        onLoad(data.path, data.github_owner, data.github_repo)
      } else {
        setInfo(`Error: ${data.detail}`)
      }
    } catch {
      setInfo('Failed to load project')
    } finally {
      setLoading(false)
    }
  }

  function selectRecent(value: string) {
    if (!value) return
    setPath(value)
    // Auto-detect type from the value
    if (value.startsWith('http') || value.includes('github.com')) {
      setType('github')
    } else if (value.startsWith('/')) {
      setType('local')
    }
  }

  return (
    <div className="project-loader">
      <div className="project-loader-type">
        <label>
          <input type="radio" name="ptype" checked={type === 'new'} onChange={() => setType('new')} />
          New
        </label>
        <label>
          <input type="radio" name="ptype" checked={type === 'local'} onChange={() => setType('local')} />
          Local
        </label>
        <label>
          <input type="radio" name="ptype" checked={type === 'github'} onChange={() => setType('github')} />
          GitHub
        </label>
      </div>
      {type !== 'new' && (
        <>
          {recentProjects.items.length > 0 && (
            <select
              className="recent-select"
              value=""
              onChange={(e) => selectRecent(e.target.value)}
            >
              <option value="">Recent projects...</option>
              {recentProjects.items.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          )}
          <input
            type="text"
            placeholder={type === 'local' ? '/path/to/project' : 'https://github.com/user/repo'}
            value={path}
            onChange={(e) => setPath(e.target.value)}
          />
          <button className="primary" onClick={handleLoad} disabled={!path.trim() || loading}>
            {loading ? 'Loading...' : 'Load'}
          </button>
        </>
      )}
      {type === 'new' && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Start from scratch. The pipeline will create all files.
        </div>
      )}
      {info && <div className="project-info">{info}</div>}
    </div>
  )
}
