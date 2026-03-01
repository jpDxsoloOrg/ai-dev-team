import { useCallback, useState } from 'react'

const MAX_ITEMS = 10

export function useRecentItems(storageKey: string) {
  const [items, setItems] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(storageKey)
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  const add = useCallback(
    (item: string) => {
      const trimmed = item.trim()
      if (!trimmed) return
      setItems((prev) => {
        const filtered = prev.filter((i) => i !== trimmed)
        const next = [trimmed, ...filtered].slice(0, MAX_ITEMS)
        localStorage.setItem(storageKey, JSON.stringify(next))
        return next
      })
    },
    [storageKey],
  )

  const remove = useCallback(
    (item: string) => {
      setItems((prev) => {
        const next = prev.filter((i) => i !== item)
        localStorage.setItem(storageKey, JSON.stringify(next))
        return next
      })
    },
    [storageKey],
  )

  return { items, add, remove }
}
