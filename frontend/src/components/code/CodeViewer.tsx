import { useState } from 'react'
import { FileTree, type FileStatus } from './FileTree'

interface CodeViewerProps {
  /** All files (original + generated merged). Key = filepath, value = content */
  files: Record<string, string>
  /** Original file contents from the loaded project (before modifications) */
  originalFiles: Record<string, string>
}

type ViewMode = 'source' | 'diff'

function computeStatuses(
  files: Record<string, string>,
  originalFiles: Record<string, string>,
): Record<string, FileStatus> {
  const statuses: Record<string, FileStatus> = {}
  for (const path of Object.keys(files)) {
    if (!(path in originalFiles)) {
      statuses[path] = 'new'
    } else if (files[path] !== originalFiles[path]) {
      statuses[path] = 'modified'
    } else {
      statuses[path] = 'unchanged'
    }
  }
  return statuses
}

function computeDiff(original: string, modified: string): DiffLine[] {
  const oldLines = original.split('\n')
  const newLines = modified.split('\n')
  const lines: DiffLine[] = []

  // Simple LCS-based diff
  const lcs = buildLCS(oldLines, newLines)
  let oi = 0
  let ni = 0
  let li = 0

  while (oi < oldLines.length || ni < newLines.length) {
    if (li < lcs.length && oi < oldLines.length && ni < newLines.length && oldLines[oi] === lcs[li] && newLines[ni] === lcs[li]) {
      lines.push({ type: 'same', oldNum: oi + 1, newNum: ni + 1, text: oldLines[oi] })
      oi++
      ni++
      li++
    } else if (ni < newLines.length && (li >= lcs.length || newLines[ni] !== lcs[li])) {
      // Check if it's also removed (replacement)
      if (oi < oldLines.length && (li >= lcs.length || oldLines[oi] !== lcs[li])) {
        lines.push({ type: 'removed', oldNum: oi + 1, newNum: null, text: oldLines[oi] })
        lines.push({ type: 'added', oldNum: null, newNum: ni + 1, text: newLines[ni] })
        oi++
        ni++
      } else {
        lines.push({ type: 'added', oldNum: null, newNum: ni + 1, text: newLines[ni] })
        ni++
      }
    } else if (oi < oldLines.length && (li >= lcs.length || oldLines[oi] !== lcs[li])) {
      lines.push({ type: 'removed', oldNum: oi + 1, newNum: null, text: oldLines[oi] })
      oi++
    }
  }

  return lines
}

interface DiffLine {
  type: 'same' | 'added' | 'removed'
  oldNum: number | null
  newNum: number | null
  text: string
}

function buildLCS(a: string[], b: string[]): string[] {
  const m = a.length
  const n = b.length
  // For large files, use a simplified approach
  if (m > 2000 || n > 2000) {
    // Fallback: just return common lines in order
    const result: string[] = []
    let j = 0
    for (let i = 0; i < m && j < n; i++) {
      const idx = b.indexOf(a[i], j)
      if (idx !== -1) {
        result.push(a[i])
        j = idx + 1
      }
    }
    return result
  }

  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  const result: string[] = []
  let i = m
  let j = n
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      result.unshift(a[i - 1])
      i--
      j--
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--
    } else {
      j--
    }
  }
  return result
}

function DiffView({ original, modified }: { original: string; modified: string }) {
  const lines = computeDiff(original, modified)

  return (
    <div className="diff-view">
      <div className="diff-header">
        <span className="diff-stat diff-stat-removed">
          -{lines.filter((l) => l.type === 'removed').length}
        </span>
        <span className="diff-stat diff-stat-added">
          +{lines.filter((l) => l.type === 'added').length}
        </span>
      </div>
      <div className="diff-content">
        {lines.map((line, i) => (
          <div key={i} className={`diff-line diff-line-${line.type}`}>
            <span className="diff-line-number diff-line-old">{line.oldNum ?? ''}</span>
            <span className="diff-line-number diff-line-new">{line.newNum ?? ''}</span>
            <span className="diff-line-marker">
              {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
            </span>
            <span className="diff-line-text">{line.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function SourceView({ content }: { content: string }) {
  return (
    <div className="code-content">
      {content.split('\n').map((line, i) => (
        <div key={i} className="code-line">
          <span className="code-line-number">{i + 1}</span>
          <span>{line}</span>
        </div>
      ))}
    </div>
  )
}

export function CodeViewer({ files, originalFiles }: CodeViewerProps) {
  const fileStatuses = computeStatuses(files, originalFiles)
  const paths = Object.keys(files)
  const [activeFile, setActiveFile] = useState<string | null>(paths[0] || null)
  const [viewMode, setViewMode] = useState<ViewMode>('source')
  const [treeFilter, setTreeFilter] = useState<'all' | 'changed'>('all')
  const [copied, setCopied] = useState(false)

  const content = activeFile ? files[activeFile] || '' : ''
  const activeStatus = activeFile ? fileStatuses[activeFile] || 'unchanged' : 'unchanged'
  const canDiff = activeStatus === 'modified'

  function handleCopy() {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="code-viewer" style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: '0.75rem' }}>
      <FileTree
        files={files}
        fileStatuses={fileStatuses}
        activeFile={activeFile}
        onSelect={(p) => { setActiveFile(p); setViewMode('source') }}
        filter={treeFilter}
        onFilterChange={setTreeFilter}
      />
      <div className="code-panel">
        {activeFile ? (
          <>
            <div className="code-panel-header">
              <div className="code-panel-header-left">
                <span>{activeFile}</span>
                {activeStatus !== 'unchanged' && (
                  <span className={`file-badge ${activeStatus === 'new' ? 'file-badge-new' : 'file-badge-modified'}`}>
                    {activeStatus === 'new' ? 'NEW' : 'MODIFIED'}
                  </span>
                )}
              </div>
              <div className="code-panel-header-right">
                {canDiff && (
                  <div className="view-mode-toggle">
                    <button
                      className={`view-mode-btn${viewMode === 'source' ? ' active' : ''}`}
                      onClick={() => setViewMode('source')}
                    >
                      Source
                    </button>
                    <button
                      className={`view-mode-btn${viewMode === 'diff' ? ' active' : ''}`}
                      onClick={() => setViewMode('diff')}
                    >
                      Diff
                    </button>
                  </div>
                )}
                <button
                  className="secondary"
                  style={{ fontSize: '0.7rem', padding: '0.2em 0.5em' }}
                  onClick={handleCopy}
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
            {viewMode === 'diff' && canDiff ? (
              <DiffView original={originalFiles[activeFile] || ''} modified={content} />
            ) : (
              <SourceView content={content} />
            )}
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
