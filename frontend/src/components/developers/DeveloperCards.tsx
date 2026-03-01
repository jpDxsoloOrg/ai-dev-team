import { useState } from 'react'
import type { DeveloperConfig } from '@/types'
import { useDevelopers } from '@/hooks/useDevelopers'
import { DeveloperCard } from './DeveloperCard'
import { AddDevModal } from './AddDevModal'

export function DeveloperCards() {
  const { developers, create, update, remove, duplicate, toggle } = useDevelopers()
  const [editing, setEditing] = useState<DeveloperConfig | null>(null)
  const [showAdd, setShowAdd] = useState(false)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.9rem' }}>Developer Agents</h3>
        <button className="primary" onClick={() => setShowAdd(true)}>
          + Add Developer
        </button>
      </div>
      <div className="dev-cards">
        {developers.map((dev) => (
          <DeveloperCard
            key={dev.id}
            dev={dev}
            onEdit={() => setEditing(dev)}
            onDuplicate={() => duplicate(dev.id)}
            onDelete={() => {
              if (confirm(`Delete ${dev.name}?`)) remove(dev.id)
            }}
            onToggle={() => toggle(dev.id)}
          />
        ))}
      </div>

      {showAdd && (
        <AddDevModal
          onSave={create}
          onClose={() => setShowAdd(false)}
        />
      )}
      {editing && (
        <AddDevModal
          existing={editing}
          onSave={(data) => update(editing.id, data)}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
