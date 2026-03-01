interface FileTreeProps {
  files: Record<string, string>
  activeFile: string | null
  onSelect: (path: string) => void
}

const FILE_ICONS: Record<string, string> = {
  ts: '\uD83D\uDFE6',
  tsx: '\u269B\uFE0F',
  js: '\uD83D\uDFE8',
  jsx: '\u269B\uFE0F',
  py: '\uD83D\uDC0D',
  css: '\uD83C\uDFA8',
  html: '\uD83C\uDF10',
  json: '\uD83D\uDCCB',
  md: '\uD83D\uDCDD',
  yml: '\u2699\uFE0F',
  yaml: '\u2699\uFE0F',
}

function getIcon(path: string): string {
  const ext = path.split('.').pop() || ''
  return FILE_ICONS[ext] || '\uD83D\uDCC4'
}

export function FileTree({ files, activeFile, onSelect }: FileTreeProps) {
  const paths = Object.keys(files).sort()

  if (paths.length === 0) {
    return (
      <div className="file-tree">
        <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No files generated yet.
        </div>
      </div>
    )
  }

  return (
    <div className="file-tree">
      {paths.map((p) => (
        <div
          key={p}
          className="file-tree-item"
          data-active={p === activeFile}
          onClick={() => onSelect(p)}
        >
          <span className="file-icon">{getIcon(p)}</span>
          <span>{p}</span>
        </div>
      ))}
    </div>
  )
}
