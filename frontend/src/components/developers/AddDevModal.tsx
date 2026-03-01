import { useState, useEffect } from 'react'
import type { DeveloperConfig } from '@/types'

interface AddDevModalProps {
  existing?: DeveloperConfig | null
  teamNames?: string[]
  onSave: (data: Partial<DeveloperConfig>) => Promise<void>
  onClose: () => void
}

export function AddDevModal({ existing, teamNames = [], onSave, onClose }: AddDevModalProps) {
  const [name, setName] = useState('')
  const [emoji, setEmoji] = useState('\uD83E\uDD16')
  const [color, setColor] = useState('#4a9eff')
  const [specialty, setSpecialty] = useState('')
  const [team, setTeam] = useState('')
  const [customPrompt, setCustomPrompt] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (existing) {
      setName(existing.name)
      setEmoji(existing.emoji)
      setColor(existing.color)
      setSpecialty(existing.specialty)
      setTeam(existing.team || '')
      setCustomPrompt(existing.custom_prompt)
    }
  }, [existing])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave({ name, emoji, color, specialty, team, custom_prompt: customPrompt })
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{existing ? 'Edit Developer' : 'Add Developer'}</h2>
        <form className="modal-form" onSubmit={handleSubmit}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <label style={{ flex: 1 }}>
              Emoji
              <input value={emoji} onChange={(e) => setEmoji(e.target.value)} />
            </label>
            <label style={{ flex: 1 }}>
              Color
              <input type="color" value={color} onChange={(e) => setColor(e.target.value)} style={{ height: '2rem' }} />
            </label>
          </div>
          <label>
            Specialty
            <input
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              placeholder="e.g. frontend, backend, testing"
            />
          </label>
          <label>
            Team
            <input
              list="team-names"
              value={team}
              onChange={(e) => setTeam(e.target.value)}
              placeholder="e.g. Frontend, Backend, QA"
            />
            <datalist id="team-names">
              {teamNames.map((t) => <option key={t} value={t} />)}
            </datalist>
          </label>
          <label>
            Custom Prompt
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              rows={3}
              placeholder="Additional instructions for this developer..."
            />
          </label>
          <div className="modal-actions">
            <button type="button" className="secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="primary" disabled={!name.trim() || saving}>
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
