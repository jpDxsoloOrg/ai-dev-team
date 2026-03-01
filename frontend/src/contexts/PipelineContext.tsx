import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
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
  start: (goal: string, provider: string, model: string, projectPath?: string) => Promise<void>
  pause: () => Promise<void>
  resume: () => Promise<void>
  stop: () => Promise<void>
  clearEvents: () => void
}

const PipelineContext = createContext<PipelineContextValue | null>(null)

export function PipelineProvider({ children }: { children: ReactNode }) {
  const { connected, events, clearEvents } = useWebSocket()
  const [run, setRun] = useState<PipelineRun | null>(null)
  const [tasks, setTasks] = useState<PipelineTask[]>([])
  const [status, setStatus] = useState<PipelineStatus | null>(null)

  // Process WS events into state
  useEffect(() => {
    if (events.length === 0) return
    const latest = events[events.length - 1]

    switch (latest.type) {
      case 'pipeline_status':
        setStatus(latest.data.status as PipelineStatus)
        break
      case 'task_created':
        setTasks((prev) => [
          ...prev,
          {
            id: latest.data.task_id,
            run_id: latest.run_id,
            title: latest.data.title,
            description: '',
            status: 'pending' as TaskStatus,
            assigned_to: null,
            specialty_tags: latest.data.specialty_tags,
            code_output: null,
            review_notes: null,
            test_results: null,
            file_paths: null,
            created_at: latest.timestamp,
            updated_at: latest.timestamp,
          },
        ])
        break
      case 'task_assigned':
        setTasks((prev) =>
          prev.map((t) =>
            t.id === latest.data.task_id
              ? { ...t, assigned_to: latest.data.developer, status: 'assigned' as TaskStatus }
              : t,
          ),
        )
        break
      case 'task_updated':
        setTasks((prev) =>
          prev.map((t) =>
            t.id === latest.data.task_id
              ? { ...t, status: latest.data.status as TaskStatus }
              : t,
          ),
        )
        break
    }
  }, [events])

  const start = useCallback(
    async (goal: string, provider: string, model: string, projectPath?: string) => {
      const newRun = await pipelineApi.start({
        goal,
        provider,
        model,
        project_path: projectPath ?? null,
      })
      setRun(newRun)
      setTasks(newRun.tasks)
      setStatus(newRun.status)
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
      clearEvents,
    }),
    [run, tasks, status, events, connected, start, pause, resume, stopPipeline, clearEvents],
  )

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>
}

export function usePipeline(): PipelineContextValue {
  const ctx = useContext(PipelineContext)
  if (!ctx) throw new Error('usePipeline must be used within PipelineProvider')
  return ctx
}
