import { useCallback, useEffect, useRef, useState } from 'react'
import type { PipelineEvent } from '@/types/events'

const MAX_EVENTS = 500
const MAX_RECONNECT_DELAY = 30_000

interface UseWebSocketReturn {
  connected: boolean
  events: PipelineEvent[]
  clearEvents: () => void
}

export function useWebSocket(): UseWebSocketReturn {
  const [connected, setConnected] = useState(false)
  const [events, setEvents] = useState<PipelineEvent[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempt = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const unmountedRef = useRef(false)

  const clearEvents = useCallback(() => setEvents([]), [])

  useEffect(() => {
    unmountedRef.current = false

    function connect() {
      if (unmountedRef.current) return

      // Close any existing connection to prevent duplicates (React StrictMode)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
        wsRef.current = null
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
      wsRef.current = ws

      ws.onopen = () => {
        if (unmountedRef.current) { ws.close(); return }
        setConnected(true)
        reconnectAttempt.current = 0
      }

      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as PipelineEvent
          setEvents((prev) => {
            const next = [...prev, event]
            return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next
          })
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
        if (!unmountedRef.current) {
          scheduleReconnect()
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    function scheduleReconnect() {
      if (unmountedRef.current) return
      const delay = Math.min(
        1000 * Math.pow(2, reconnectAttempt.current),
        MAX_RECONNECT_DELAY,
      )
      reconnectAttempt.current++
      reconnectTimer.current = setTimeout(connect, delay)
    }

    connect()

    return () => {
      unmountedRef.current = true
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [])

  return { connected, events, clearEvents }
}
