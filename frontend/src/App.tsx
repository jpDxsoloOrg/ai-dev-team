import { useState, useCallback } from 'react'
import { PipelineProvider, usePipeline } from '@/contexts/PipelineContext'
import { SettingsProvider } from '@/contexts/SettingsContext'
import { AppLayout } from '@/components/layout/AppLayout'
import { PipelineControls } from '@/components/pipeline/PipelineControls'
import { ProgressBar } from '@/components/pipeline/ProgressBar'
import { TaskBoard } from '@/components/pipeline/TaskBoard'
import { EventFeed } from '@/components/pipeline/EventFeed'
import { DeveloperCards } from '@/components/developers/DeveloperCards'
import { DeveloperDetailModal } from '@/components/developers/DeveloperDetailModal'
import { ProviderSelect } from '@/components/settings/ProviderSelect'
import { ApiKeyManager } from '@/components/settings/ApiKeyManager'
import { ProjectLoader } from '@/components/settings/ProjectLoader'
import { CodeViewer } from '@/components/code/CodeViewer'
import { ExportPanel } from '@/components/export/ExportPanel'
import { ChatBox } from '@/components/chat/ChatBox'
import { useDevelopers } from '@/hooks/useDevelopers'
import { projectsApi } from '@/services/api'
import type { DeveloperConfig } from '@/types'
import './App.css'

type Tab = 'tasks' | 'code' | 'chat' | 'team' | 'export'

function TeamSidebarSection() {
  const { developers } = useDevelopers()
  const [selectedDev, setSelectedDev] = useState<DeveloperConfig | null>(null)

  const grouped = (() => {
    const groups: Record<string, DeveloperConfig[]> = {}
    for (const dev of developers) {
      const key = dev.team || 'Unassigned'
      if (!groups[key]) groups[key] = []
      groups[key].push(dev)
    }
    return groups
  })()

  const sortedTeams = Object.keys(grouped).sort((a, b) => {
    if (a === 'Unassigned') return 1
    if (b === 'Unassigned') return -1
    return a.localeCompare(b)
  })

  return (
    <>
      <div className="dev-mini-list">
        {sortedTeams.map((teamName) => (
          <div key={teamName}>
            <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
              {teamName}
            </div>
            {grouped[teamName].map((d) => (
              <div
                key={d.id}
                className="dev-mini dev-mini-clickable"
                onClick={() => setSelectedDev(d)}
              >
                <span className="dev-mini-status" data-disabled={!d.enabled} />
                <span>{d.emoji} {d.name}</span>
              </div>
            ))}
          </div>
        ))}
        {developers.length === 0 && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Loading...</span>
        )}
      </div>
      {selectedDev && (
        <DeveloperDetailModal dev={selectedDev} onClose={() => setSelectedDev(null)} />
      )}
    </>
  )
}

function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('tasks')
  const [projectPath, setProjectPath] = useState('')
  const [githubOwner, setGithubOwner] = useState('')
  const [githubRepo, setGithubRepo] = useState('')
  const [originalFiles, setOriginalFiles] = useState<Record<string, string>>({})
  const { events } = usePipeline()

  const handleProjectLoad = useCallback(async (path: string, owner?: string, repo?: string) => {
    setProjectPath(path)
    setGithubOwner(owner || '')
    setGithubRepo(repo || '')
    try {
      const data = await projectsApi.getFiles(path)
      setOriginalFiles(data.files)
    } catch {
      setOriginalFiles({})
    }
  }, [])

  // Collect generated files with content from code_generated events
  const generatedFiles: Record<string, string> = {}
  for (const ev of events) {
    if (ev.type === 'code_generated' && ev.data.contents) {
      Object.assign(generatedFiles, ev.data.contents)
    }
  }

  // Merge original files with generated: generated files override originals
  const allFiles: Record<string, string> = { ...originalFiles, ...generatedFiles }

  // If no project loaded and no generated files, just show generated
  const hasProject = projectPath && Object.keys(originalFiles).length > 0

  return (
    <AppLayout
      projectSection={<ProjectLoader onLoad={handleProjectLoad} />}
      providerSection={<ProviderSelect />}
      teamSection={<TeamSidebarSection />}
      settingsSection={<ApiKeyManager />}
      main={
        <>
          <PipelineControls projectPath={projectPath} githubOwner={githubOwner} githubRepo={githubRepo} />
          <ProgressBar />

          <div className="tabs" style={{ marginTop: '1rem' }}>
            {(['tasks', 'code', 'chat', 'team', 'export'] as Tab[]).map((tab) => (
              <button
                key={tab}
                className="tab"
                data-active={activeTab === tab}
                onClick={() => setActiveTab(tab)}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {activeTab === 'tasks' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <TaskBoard />
              <EventFeed />
            </div>
          )}
          {activeTab === 'code' && (
            <CodeViewer
              files={hasProject ? allFiles : generatedFiles}
              originalFiles={hasProject ? originalFiles : {}}
            />
          )}
          {activeTab === 'chat' && (
            <ChatBox projectPath={projectPath} githubOwner={githubOwner} githubRepo={githubRepo} />
          )}
          {activeTab === 'team' && <DeveloperCards />}
          {activeTab === 'export' && <ExportPanel />}
        </>
      }
    />
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
