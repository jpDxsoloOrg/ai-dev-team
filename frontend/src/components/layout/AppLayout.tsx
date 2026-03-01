import type { ReactNode } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

interface AppLayoutProps {
  main: ReactNode
  projectSection: ReactNode
  providerSection: ReactNode
  teamSection: ReactNode
  settingsSection: ReactNode
}

export function AppLayout({ main, projectSection, providerSection, teamSection, settingsSection }: AppLayoutProps) {
  return (
    <div className="app-layout">
      <Header />
      <div className="app-body">
        <Sidebar
          projectSection={projectSection}
          providerSection={providerSection}
          teamSection={teamSection}
          settingsSection={settingsSection}
        />
        <main className="app-main">{main}</main>
      </div>
    </div>
  )
}
