import type { DeveloperConfig } from '@/types'

interface DeveloperCardProps {
  dev: DeveloperConfig
  onClick: () => void
  onEdit: () => void
  onDuplicate: () => void
  onDelete: () => void
  onToggle: () => void
}

export function DeveloperCard({ dev, onClick, onEdit, onDuplicate, onDelete, onToggle }: DeveloperCardProps) {
  return (
    <div
      className="dev-card"
      style={{ borderColor: dev.enabled ? dev.color : 'var(--border-color)', cursor: 'pointer' }}
      onClick={onClick}
    >
      <div className="dev-card-header">
        <span className="dev-card-emoji">{dev.emoji}</span>
        <span className="dev-card-name" style={{ opacity: dev.enabled ? 1 : 0.5 }}>
          {dev.name}
        </span>
        <button
          className="toggle"
          data-on={dev.enabled}
          onClick={(e) => { e.stopPropagation(); onToggle() }}
          title={dev.enabled ? 'Disable' : 'Enable'}
        />
      </div>
      <div className="dev-card-specialty">{dev.specialty}</div>
      <div className="dev-card-actions">
        <button className="secondary" onClick={(e) => { e.stopPropagation(); onEdit() }}>Edit</button>
        <button className="secondary" onClick={(e) => { e.stopPropagation(); onDuplicate() }}>Duplicate</button>
        <button className="danger" onClick={(e) => { e.stopPropagation(); onDelete() }}>Delete</button>
      </div>
    </div>
  )
}
