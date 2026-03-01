/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { PipelineRun, PipelineStatus, PipelineTask, TaskStatus } from '@/types'
import type { PipelineEvent } from '@/types/events'
import { pipelineApi } from '@/services/api'
import { useWebSocket } from '@/hooks/useWebSocket'

interface PipelineContextValue {
  run: PipelineRun | null
  tasks: PipelineTask[]
  status: PipelineStatus | null
  events: PipelineEvent[]
  connected: boolean
  start: (goal: string, provider: string, model: string, projectPath?: string, team?: string, autoAssign?: boolean) => Promise<void>
  pause: () => Promise<void>
  resume: () => Promise<void>
  stop: () => Promise<void>
  assignTask: (taskId: string, devId: string) => Promise<void>
  setAutoAssign: (enabled: boolean) => Promise<void>
  clearEvents: () => void
}

const PipelineContext = createContext<PipelineContextValue | null>(null)

export function PipelineProvider({ children }: { children: ReactNode }) {
  const { connected, events, clearEvents } = useWebSocket()
  const [run, setRun] = useState<PipelineRun | null>(null)
  const [tasks, setTasks] = useState<PipelineTask[]>([])
  const [status, setStatus] = useState<PipelineStatus | null>(null)

  // Track how many events we've already processed
  const processedCount = useRef(0)

  // Process ALL new WS events into state (setState is intentional for WS event sync)
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (events.length <= processedCount.current) return

    const newEvents = events.slice(processedCount.current)
    processedCount.current = events.length

    for (const event of newEvents) {
      switch (event.type) {
        case 'pipeline_status':
          setStatus(event.data.status as PipelineStatus)
          break
        case 'task_created':
          setTasks((prev) => {
            // Avoid duplicates
            if (prev.some((t) => t.id === event.data.task_id)) return prev
            return [
              ...prev,
              {
                id: event.data.task_id,
                run_id: event.run_id,
                title: event.data.title,
                description: '',
                status: 'pending' as TaskStatus,
                assigned_to: null,
                specialty_tags: event.data.specialty_tags,
                code_output: null,
                review_notes: null,
                test_results: null,
                file_paths: null,
                created_at: event.timestamp,
                updated_at: event.timestamp,
              },
            ]
          })
          break
        case 'task_assigned':
          setTasks((prev) =>
            prev.map((t) =>
              t.id === event.data.task_id
                ? { ...t, assigned_to: event.data.developer, status: 'assigned' as TaskStatus }
                : t,
            ),
          )
          break
        case 'task_updated':
          setTasks((prev) =>
            prev.map((t) =>
              t.id === event.data.task_id
                ? { ...t, status: event.data.status as TaskStatus }
                : t,
            ),
          )
          break
      }
    }
  }, [events])
  /* eslint-enable react-hooks/set-state-in-effect */

  const start = useCallback(
    async (goal: string, provider: string, model: string, projectPath?: string, team?: string, autoAssign?: boolean) => {
      const newRun = await pipelineApi.start({
        goal,
        provider,
        model,
        project_path: projectPath ?? null,
        team: team ?? null,
        auto_assign: autoAssign ?? true,
      })
      setRun(newRun)
      setTasks(newRun.tasks)
      setStatus(newRun.status)
      processedCount.current = 0
      clearEvents()
    },
    [clearEvents],
  )

  const pause = useCallback(async () => {
    if (run) await pipelineApi.pause(run.id)
  }, [run])

  const resume = useCallback(async () => {
    if (run) await pipelineApi.resume(run.id)
  }, [run])

  const stopPipeline = useCallback(async () => {
    if (run) await pipelineApi.stop(run.id)
  }, [run])

  const assignTask = useCallback(async (taskId: string, devId: string) => {
    if (run) await pipelineApi.assign(run.id, taskId, devId)
  }, [run])

  const setAutoAssign = useCallback(async (enabled: boolean) => {
    if (run) await pipelineApi.setAutoAssign(run.id, enabled)
  }, [run])

  const value = useMemo(
    () => ({
      run,
      tasks,
      status,
      events,
      connected,
      start,
      pause,
      resume,
      stop: stopPipeline,
      assignTask,
      setAutoAssign,
      clearEvents,
    }),
    [run, tasks, status, events, connected, start, pause, resume, stopPipeline, assignTask, setAutoAssign, clearEvents],
  )

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>
}

export function usePipeline(): PipelineContextValue {
  const ctx = useContext(PipelineContext)
  if (!ctx) throw new Error('usePipeline must be used within PipelineProvider')
  return ctx
}
