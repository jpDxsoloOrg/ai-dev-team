import { useEffect, useRef } from 'react'
import { usePipeline } from '@/contexts/PipelineContext'
import type { PipelineEvent } from '@/types/events'

const AGENT_EMOJI: Record<string, string> = {
  planner: '\uD83D\uDCCB',
  developer: '\uD83D\uDCBB',
  reviewer: '\uD83D\uDD0D',
  tester: '\uD83E\uDDEA',
}

function eventEmoji(event: PipelineEvent): string {
  if ('agent' in event.data) {
    const name = (event.data as { agent: string }).agent.toLowerCase()
    return AGENT_EMOJI[name] || '\uD83E\uDD16'
  }
  switch (event.type) {
    case 'pipeline_status': return '\u2699\uFE0F'
    case 'task_created': return '\u2795'
    case 'task_assigned': return '\uD83D\uDC64'
    case 'task_updated': return '\uD83D\uDD04'
    case 'error': return '\u274C'
    default: return '\uD83D\uDCDD'
  }
}

function eventMessage(event: PipelineEvent): string {
  switch (event.type) {
    case 'pipeline_status': return `Pipeline: ${event.data.status}`
    case 'task_created': return `Task: ${event.data.title}`
    case 'task_assigned': return `${event.data.developer} assigned to task`
    case 'task_updated': return `Task status: ${event.data.status}`
    case 'agent_thinking': return `${event.data.agent}: ${event.data.message}`
    case 'agent_output': return `${event.data.agent}: ${event.data.output.slice(0, 120)}`
    case 'code_generated': return `${event.data.agent}: generated ${event.data.files.length} files`
    case 'review_result': return `Review: ${event.data.approved ? 'approved' : 'rejected'}`
    case 'test_result': return `Tests: ${event.data.passed ? 'passed' : 'failed'} (${event.data.test_count} tests)`
    case 'error': return event.data.message
    case 'log': return event.data.message
  }
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString('en-US', { hour12: false })
  } catch {
    return ''
  }
}

export function EventFeed() {
  const { events, clearEvents } = usePipeline()
  const containerRef = useRef<HTMLDivElement>(null)
  const autoScrollRef = useRef(true)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    function onScroll() {
      if (!el) return
      autoScrollRef.current = el.scrollTop + el.clientHeight >= el.scrollHeight - 20
    }
    el.addEventListener('scroll', onScroll)
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (autoScrollRef.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [events])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Events ({events.length})
        </span>
        {events.length > 0 && (
          <button className="secondary" style={{ fontSize: '0.7rem', padding: '0.2em 0.5em' }} onClick={clearEvents}>
            Clear
          </button>
        )}
      </div>
      <div className="event-feed" ref={containerRef}>
        {events.length === 0 && (
          <div style={{ padding: '1rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Waiting for events...
          </div>
        )}
        {events.map((event, i) => (
          <div key={i} className="event-row">
            <span className="event-time">{formatTime(event.timestamp)}</span>
            <span className="event-type">{eventEmoji(event)} {event.type}</span>
            <span className="event-message">{eventMessage(event)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
