import { useState, type ReactNode } from 'react'

interface SectionProps {
  title: string
  defaultOpen?: boolean
  children: ReactNode
}

function Section({ title, defaultOpen = true, children }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="sidebar-section">
      <button className="sidebar-section-header" onClick={() => setOpen(!open)}>
        <span>{title}</span>
        <span className="sidebar-chevron">{open ? '\u25BC' : '\u25B6'}</span>
      </button>
      {open && <div className="sidebar-section-content">{children}</div>}
    </div>
  )
}

interface SidebarProps {
  projectSection: ReactNode
  providerSection: ReactNode
  teamSection: ReactNode
  settingsSection: ReactNode
}

export function Sidebar({ projectSection, providerSection, teamSection, settingsSection }: SidebarProps) {
  return (
    <aside className="sidebar">
      <Section title="Project">{projectSection}</Section>
      <Section title="Provider">{providerSection}</Section>
      <Section title="Team">{teamSection}</Section>
      <Section title="Settings" defaultOpen={false}>{settingsSection}</Section>
    </aside>
  )
}
