import { useCallback, useEffect, useState } from 'react'
import type { DeveloperConfig } from '@/types'
import { developersApi } from '@/services/api'

interface UseDevelopersReturn {
  developers: DeveloperConfig[]
  loading: boolean
  create: (data: Partial<DeveloperConfig>) => Promise<void>
  update: (id: string, data: Partial<DeveloperConfig>) => Promise<void>
  remove: (id: string) => Promise<void>
  duplicate: (id: string) => Promise<void>
  toggle: (id: string) => Promise<void>
  refresh: () => Promise<void>
}

export function useDevelopers(): UseDevelopersReturn {
  const [developers, setDevelopers] = useState<DeveloperConfig[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const list = await developersApi.list()
      setDevelopers(list)
    } catch {
      // Backend may not be up
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const create = useCallback(async (data: Partial<DeveloperConfig>) => {
    await developersApi.create(data)
    await refresh()
  }, [refresh])

  const update = useCallback(async (id: string, data: Partial<DeveloperConfig>) => {
    await developersApi.update(id, data)
    await refresh()
  }, [refresh])

  const remove = useCallback(async (id: string) => {
    await developersApi.delete(id)
    await refresh()
  }, [refresh])

  const duplicateDev = useCallback(async (id: string) => {
    await developersApi.duplicate(id)
    await refresh()
  }, [refresh])

  const toggle = useCallback(async (id: string) => {
    await developersApi.toggle(id)
    await refresh()
  }, [refresh])

  return { developers, loading, create, update, remove, duplicate: duplicateDev, toggle, refresh }
}
