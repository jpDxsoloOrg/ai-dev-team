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
  const [showNewTeam, setShowNewTeam] = useState(false)
  const [customPrompt, setCustomPrompt] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (existing) {
      setName(existing.name)
      setEmoji(existing.emoji)
      setColor(existing.color)
      setSpecialty(existing.specialty)
      const existingTeam = existing.team || ''
      setTeam(existingTeam)
      setShowNewTeam(existingTeam !== '' && !teamNames.includes(existingTeam))
      setCustomPrompt(existing.custom_prompt)
    }
  }, [existing, teamNames])

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
            <select
              value={showNewTeam ? '__new__' : team}
              onChange={(e) => {
                if (e.target.value === '__new__') {
                  setShowNewTeam(true)
                  setTeam('')
                } else {
                  setShowNewTeam(false)
                  setTeam(e.target.value)
                }
              }}
            >
              <option value="">No team</option>
              {teamNames.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
              <option value="__new__">+ New team...</option>
            </select>
            {showNewTeam && (
              <input
                value={team}
                onChange={(e) => setTeam(e.target.value)}
                placeholder="Enter new team name"
                autoFocus
                style={{ marginTop: '0.4rem' }}
              />
            )}
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
