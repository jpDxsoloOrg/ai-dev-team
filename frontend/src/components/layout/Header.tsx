import { usePipeline } from '@/contexts/PipelineContext'

const STATUS_COLORS: Record<string, string> = {
  planning: 'var(--accent-blue)',
  assigning: 'var(--accent-purple)',
  developing: 'var(--accent-orange)',
  reviewing: 'var(--accent-yellow)',
  testing: 'var(--accent-blue)',
  merging: 'var(--accent-purple)',
  completed: 'var(--accent-green)',
  failed: 'var(--accent-red)',
  paused: 'var(--text-muted)',
}

export function Header() {
  const { connected, status } = usePipeline()

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="header-title">AI Dev Team</h1>
      </div>
      <div className="header-right">
        {status && (
          <span
            className="header-badge"
            style={{ background: STATUS_COLORS[status] || 'var(--bg-tertiary)' }}
          >
            {status}
          </span>
        )}
        <span className="header-dot" data-connected={connected} />
      </div>
    </header>
  )
}
