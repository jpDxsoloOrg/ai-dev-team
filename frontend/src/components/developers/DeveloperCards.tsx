import { useState, useMemo } from 'react'
import type { DeveloperConfig } from '@/types'
import { useDevelopers } from '@/hooks/useDevelopers'
import { DeveloperCard } from './DeveloperCard'
import { DeveloperDetailModal } from './DeveloperDetailModal'
import { AddDevModal } from './AddDevModal'

export function DeveloperCards() {
  const { developers, create, update, remove, duplicate, toggle } = useDevelopers()
  const [editing, setEditing] = useState<DeveloperConfig | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [viewing, setViewing] = useState<DeveloperConfig | null>(null)

  const teamNames = useMemo(
    () => [...new Set(developers.map((d) => d.team).filter(Boolean))],
    [developers],
  )

  const grouped = useMemo(() => {
    const groups: Record<string, DeveloperConfig[]> = {}
    for (const dev of developers) {
      const key = dev.team || 'Unassigned'
      if (!groups[key]) groups[key] = []
      groups[key].push(dev)
    }
    return groups
  }, [developers])

  const sortedTeams = useMemo(() => {
    const keys = Object.keys(grouped)
    return keys.sort((a, b) => {
      if (a === 'Unassigned') return 1
      if (b === 'Unassigned') return -1
      return a.localeCompare(b)
    })
  }, [grouped])

  function renderDevCard(dev: DeveloperConfig) {
    return (
      <DeveloperCard
        key={dev.id}
        dev={dev}
        onClick={() => setViewing(dev)}
        onEdit={() => setEditing(dev)}
        onDuplicate={() => duplicate(dev.id)}
        onDelete={() => {
          if (confirm(`Delete ${dev.name}?`)) remove(dev.id)
        }}
        onToggle={() => toggle(dev.id)}
      />
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.9rem' }}>Developer Agents</h3>
        <button className="primary" onClick={() => setShowAdd(true)}>
          + Add Developer
        </button>
      </div>

      {sortedTeams.map((teamName) => (
        <div key={teamName} style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {teamName}
          </div>
          <div className="dev-cards">
            {grouped[teamName].map(renderDevCard)}
          </div>
        </div>
      ))}

      {showAdd && (
        <AddDevModal
          teamNames={teamNames}
          onSave={create}
          onClose={() => setShowAdd(false)}
        />
      )}
      {editing && (
        <AddDevModal
          existing={editing}
          teamNames={teamNames}
          onSave={(data) => update(editing.id, data)}
          onClose={() => setEditing(null)}
        />
      )}
      {viewing && (
        <DeveloperDetailModal
          dev={viewing}
          onClose={() => setViewing(null)}
        />
      )}
    </div>
  )
}
