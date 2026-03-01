import { useState } from 'react'
import { useSettings } from '@/contexts/SettingsContext'

export function ApiKeyManager() {
  const { providers, apiKeyStatus, saveApiKey, deleteApiKey } = useSettings()
  const [inputs, setInputs] = useState<Record<string, string>>({})

  const keyProviders = providers.filter((p) => p.name !== 'ollama')

  return (
    <div className="key-manager">
      {keyProviders.map((p) => {
        const status = apiKeyStatus[p.name]
        return (
          <div key={p.name} className="key-row">
            <label>{p.name}</label>
            {status?.configured && (
              <div className="key-status">
                Configured: {status.masked}
                <button
                  className="danger"
                  style={{ fontSize: '0.65rem', padding: '0.1em 0.4em', marginLeft: '0.5rem' }}
                  onClick={() => deleteApiKey(p.name)}
                >
                  Remove
                </button>
              </div>
            )}
            <div className="key-row-input">
              <input
                type="password"
                placeholder={`${p.name} API key`}
                value={inputs[p.name] || ''}
                onChange={(e) => setInputs((prev) => ({ ...prev, [p.name]: e.target.value }))}
              />
              <button
                className="primary"
                disabled={!inputs[p.name]}
                onClick={async () => {
                  await saveApiKey(p.name, inputs[p.name])
                  setInputs((prev) => ({ ...prev, [p.name]: '' }))
                }}
              >
                Save
              </button>
            </div>
          </div>
        )
      })}
      {keyProviders.length === 0 && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          No providers requiring API keys found.
        </div>
      )}
    </div>
  )
}
