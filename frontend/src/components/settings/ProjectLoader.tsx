import { useState } from 'react'

type ProjectType = 'new' | 'local' | 'github'

interface ProjectLoaderProps {
  onLoad: (projectPath: string) => void
}

export function ProjectLoader({ onLoad }: ProjectLoaderProps) {
  const [type, setType] = useState<ProjectType>('new')
  const [path, setPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState<string | null>(null)

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
        onLoad(data.path)
      } else {
        setInfo(`Error: ${data.detail}`)
      }
    } catch {
      setInfo('Failed to load project')
    } finally {
      setLoading(false)
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
