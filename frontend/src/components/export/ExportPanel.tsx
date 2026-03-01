import { usePipeline } from '@/contexts/PipelineContext'

export function ExportPanel() {
  const { run } = usePipeline()

  if (!run) {
    return (
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        No pipeline run to export.
      </div>
    )
  }

  function downloadZip() {
    window.open(`/api/export/${run!.id}/zip`, '_blank')
  }

  function downloadTranscript() {
    window.open(`/api/export/${run!.id}/transcript`, '_blank')
  }

  async function pushToGit() {
    try {
      const res = await fetch(`/api/export/${run!.id}/git`, { method: 'POST' })
      const data = await res.json()
      if (res.ok) {
        alert(`Git push: ${data.message || 'success'}`)
      } else {
        alert(`Error: ${data.detail}`)
      }
    } catch {
      alert('Failed to push to git')
    }
  }

  return (
    <div className="export-panel">
      <button className="secondary" onClick={downloadZip}>
        Download ZIP
      </button>
      <button className="secondary" onClick={downloadTranscript}>
        Download Transcript
      </button>
      <button className="secondary" onClick={pushToGit}>
        Push to Git
      </button>
    </div>
  )
}
