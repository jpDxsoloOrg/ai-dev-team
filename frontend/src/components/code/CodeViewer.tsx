import { useState } from 'react'
import { FileTree } from './FileTree'

interface CodeViewerProps {
  files: Record<string, string>
}

export function CodeViewer({ files }: CodeViewerProps) {
  const paths = Object.keys(files)
  const [activeFile, setActiveFile] = useState<string | null>(paths[0] || null)
  const content = activeFile ? files[activeFile] || '' : ''
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="code-viewer" style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '0.75rem' }}>
      <FileTree files={files} activeFile={activeFile} onSelect={setActiveFile} />
      <div className="code-panel">
        {activeFile ? (
          <>
            <div className="code-panel-header">
              <span>{activeFile}</span>
              <button
                className="secondary"
                style={{ fontSize: '0.7rem', padding: '0.2em 0.5em' }}
                onClick={handleCopy}
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <div className="code-content">
              {content.split('\n').map((line, i) => (
                <div key={i} className="code-line">
                  <span className="code-line-number">{i + 1}</span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '2rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Select a file to view its contents.
          </div>
        )}
      </div>
    </div>
  )
}
