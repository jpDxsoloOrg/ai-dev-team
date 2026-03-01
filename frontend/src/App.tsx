import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState<string>('checking...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('disconnected'))
  }, [])

  return (
    <div className="app">
      <h1>AI Dev Team Pipeline</h1>
      <p>
        Backend: <span className={`status ${status}`}>{status}</span>
      </p>
    </div>
  )
}

export default App
