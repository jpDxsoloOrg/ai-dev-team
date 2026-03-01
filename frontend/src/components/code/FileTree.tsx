import { useState } from 'react'

export type FileStatus = 'new' | 'modified' | 'unchanged'

interface FileTreeProps {
  files: Record<string, string>
  fileStatuses: Record<string, FileStatus>
  activeFile: string | null
  onSelect: (path: string) => void
  filter: 'all' | 'changed'
  onFilterChange: (filter: 'all' | 'changed') => void
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

const STATUS_BADGE: Record<FileStatus, { label: string; className: string } | null> = {
  new: { label: 'N', className: 'file-badge-new' },
  modified: { label: 'M', className: 'file-badge-modified' },
  unchanged: null,
}

interface TreeNode {
  name: string
  path: string
  children: TreeNode[]
  isFile: boolean
}

function buildTree(paths: string[]): TreeNode[] {
  const root: TreeNode = { name: '', path: '', children: [], isFile: false }

  for (const filePath of paths) {
    const parts = filePath.split('/')
    let current = root

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      const isLast = i === parts.length - 1
      const partPath = parts.slice(0, i + 1).join('/')

      let existing = current.children.find((c) => c.name === part)
      if (!existing) {
        existing = { name: part, path: partPath, children: [], isFile: isLast }
        current.children.push(existing)
      }
      current = existing
    }
  }

  // Sort: folders first, then files, alphabetical within each group
  function sortTree(nodes: TreeNode[]) {
    nodes.sort((a, b) => {
      if (a.isFile !== b.isFile) return a.isFile ? 1 : -1
      return a.name.localeCompare(b.name)
    })
    for (const node of nodes) {
      if (node.children.length > 0) sortTree(node.children)
    }
  }

  sortTree(root.children)
  return root.children
}

/** Check if a folder contains any changed files */
function folderHasChanged(node: TreeNode, statuses: Record<string, FileStatus>): boolean {
  if (node.isFile) {
    const s = statuses[node.path]
    return s === 'new' || s === 'modified'
  }
  return node.children.some((c) => folderHasChanged(c, statuses))
}

function TreeItem({
  node,
  depth,
  activeFile,
  fileStatuses,
  onSelect,
  filter,
  expandedFolders,
  toggleFolder,
}: {
  node: TreeNode
  depth: number
  activeFile: string | null
  fileStatuses: Record<string, FileStatus>
  onSelect: (path: string) => void
  filter: 'all' | 'changed'
  expandedFolders: Set<string>
  toggleFolder: (path: string) => void
}) {
  if (node.isFile) {
    const status = fileStatuses[node.path] || 'unchanged'
    if (filter === 'changed' && status === 'unchanged') return null

    const badge = STATUS_BADGE[status]
    return (
      <div
        className="file-tree-item"
        data-active={node.path === activeFile}
        data-status={status}
        style={{ paddingLeft: `${0.75 + depth * 0.75}rem` }}
        onClick={() => onSelect(node.path)}
      >
        <span className="file-icon">{getIcon(node.name)}</span>
        <span className="file-tree-name">{node.name}</span>
        {badge && <span className={`file-badge ${badge.className}`}>{badge.label}</span>}
      </div>
    )
  }

  // Folder
  if (filter === 'changed' && !folderHasChanged(node, fileStatuses)) return null

  const isExpanded = expandedFolders.has(node.path)

  return (
    <>
      <div
        className="file-tree-folder"
        style={{ paddingLeft: `${0.75 + depth * 0.75}rem` }}
        onClick={() => toggleFolder(node.path)}
      >
        <span className="folder-arrow">{isExpanded ? '\u25BE' : '\u25B8'}</span>
        <span className="folder-icon">{isExpanded ? '\uD83D\uDCC2' : '\uD83D\uDCC1'}</span>
        <span className="file-tree-name">{node.name}</span>
        {filter === 'all' && folderHasChanged(node, fileStatuses) && (
          <span className="folder-dot" />
        )}
      </div>
      {isExpanded &&
        node.children.map((child) => (
          <TreeItem
            key={child.path}
            node={child}
            depth={depth + 1}
            activeFile={activeFile}
            fileStatuses={fileStatuses}
            onSelect={onSelect}
            filter={filter}
            expandedFolders={expandedFolders}
            toggleFolder={toggleFolder}
          />
        ))}
    </>
  )
}

export function FileTree({ files, fileStatuses, activeFile, onSelect, filter, onFilterChange }: FileTreeProps) {
  const paths = Object.keys(files).sort()
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => {
    // Auto-expand top-level folders
    const topLevel = new Set<string>()
    for (const p of paths) {
      const first = p.split('/')[0]
      if (p.includes('/')) topLevel.add(first)
    }
    return topLevel
  })

  const changedCount = Object.values(fileStatuses).filter((s) => s === 'new' || s === 'modified').length

  const tree = buildTree(paths)

  function toggleFolder(path: string) {
    setExpandedFolders((prev) => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  if (paths.length === 0) {
    return (
      <div className="file-tree">
        <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No files yet.
        </div>
      </div>
    )
  }

  return (
    <div className="file-tree">
      <div className="file-tree-filters">
        <button
          className={`file-tree-filter-btn${filter === 'all' ? ' active' : ''}`}
          onClick={() => onFilterChange('all')}
        >
          All ({paths.length})
        </button>
        <button
          className={`file-tree-filter-btn${filter === 'changed' ? ' active' : ''}`}
          onClick={() => onFilterChange('changed')}
        >
          Changed ({changedCount})
        </button>
      </div>
      <div className="file-tree-nodes">
        {tree.map((node) => (
          <TreeItem
            key={node.path}
            node={node}
            depth={0}
            activeFile={activeFile}
            fileStatuses={fileStatuses}
            onSelect={onSelect}
            filter={filter}
            expandedFolders={expandedFolders}
            toggleFolder={toggleFolder}
          />
        ))}
      </div>
    </div>
  )
}
