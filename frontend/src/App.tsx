import { useEffect, useState } from 'react'
import { PipelineProvider, usePipeline } from '@/contexts/PipelineContext'
import { SettingsProvider, useSettings } from '@/contexts/SettingsContext'
import './App.css'

function Dashboard() {
  const [backendStatus, setBackendStatus] = useState<string>('checking...')
  const { connected, status, tasks, events } = usePipeline()
  const { providers, selectedProvider, selectedModel } = useSettings()

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('disconnected'))
  }, [])

  return (
    <div className="app">
      <h1>AI Dev Team Pipeline</h1>
      <div className="status-bar">
        <span>
          Backend: <span className={`status ${backendStatus}`}>{backendStatus}</span>
        </span>
        <span>
          WebSocket: <span className={`status ${connected ? 'ok' : 'disconnected'}`}>
            {connected ? 'connected' : 'disconnected'}
          </span>
        </span>
        {status && <span>Pipeline: {status}</span>}
      </div>
      <div className="info">
        <p>Providers: {providers.map((p) => `${p.name}${p.available ? ' ✓' : ''}`).join(', ') || 'loading...'}</p>
        {selectedProvider && <p>Selected: {selectedProvider} / {selectedModel}</p>}
        <p>Tasks: {tasks.length} | Events: {events.length}</p>
      </div>
    </div>
  )
}

function App() {
  return (
    <SettingsProvider>
      <PipelineProvider>
        <Dashboard />
      </PipelineProvider>
    </SettingsProvider>
  )
}

export default App
