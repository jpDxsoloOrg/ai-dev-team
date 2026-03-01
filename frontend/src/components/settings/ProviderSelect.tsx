import { useSettings } from '@/contexts/SettingsContext'

export function ProviderSelect() {
  const { providers, selectedProvider, selectedModel, setSelectedProvider, setSelectedModel } = useSettings()

  const currentProvider = providers.find((p) => p.name === selectedProvider)
  const models = currentProvider?.models ?? []

  return (
    <div className="provider-select">
      <label>
        Provider
        <select
          value={selectedProvider ?? ''}
          onChange={(e) => {
            setSelectedProvider(e.target.value)
            const prov = providers.find((p) => p.name === e.target.value)
            if (prov && prov.models.length > 0) setSelectedModel(prov.models[0])
          }}
        >
          <option value="">Select provider...</option>
          {providers.map((p) => (
            <option key={p.name} value={p.name} disabled={!p.available}>
              {p.name} {p.available ? '' : '(unavailable)'}
            </option>
          ))}
        </select>
      </label>
      {models.length > 0 && (
        <label>
          Model
          <select value={selectedModel ?? ''} onChange={(e) => setSelectedModel(e.target.value)}>
            {models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
      )}
    </div>
  )
}
