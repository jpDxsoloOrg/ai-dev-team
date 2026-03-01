import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { ProviderInfo } from '@/types'
import { providersApi, settingsApi } from '@/services/api'

interface SettingsContextValue {
  providers: ProviderInfo[]
  selectedProvider: string | null
  selectedModel: string | null
  apiKeyStatus: Record<string, { configured: boolean; masked: string | null }>
  setSelectedProvider: (name: string) => void
  setSelectedModel: (model: string) => void
  saveApiKey: (provider: string, key: string) => Promise<void>
  deleteApiKey: (provider: string) => Promise<void>
  refreshProviders: () => Promise<void>
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [apiKeyStatus, setApiKeyStatus] = useState<
    Record<string, { configured: boolean; masked: string | null }>
  >({})

  const refreshProviders = useCallback(async () => {
    try {
      const [providerList, keys] = await Promise.all([
        providersApi.list(),
        settingsApi.listKeys(),
      ])
      setProviders(providerList)
      setApiKeyStatus(keys.keys)
    } catch {
      // Silently fail - backend may not be up yet
    }
  }, [])

  useEffect(() => {
    refreshProviders()
  }, [refreshProviders])

  // Auto-select first available provider's first model
  useEffect(() => {
    if (!selectedProvider && providers.length > 0) {
      const available = providers.find((p) => p.available && p.models.length > 0)
      if (available) {
        setSelectedProvider(available.name)
        setSelectedModel(available.models[0])
      }
    }
  }, [providers, selectedProvider])

  const saveApiKey = useCallback(
    async (provider: string, key: string) => {
      await settingsApi.saveKey(provider, key)
      await refreshProviders()
    },
    [refreshProviders],
  )

  const deleteApiKey = useCallback(
    async (provider: string) => {
      await settingsApi.deleteKey(provider)
      await refreshProviders()
    },
    [refreshProviders],
  )

  const value = useMemo(
    () => ({
      providers,
      selectedProvider,
      selectedModel,
      apiKeyStatus,
      setSelectedProvider,
      setSelectedModel,
      saveApiKey,
      deleteApiKey,
      refreshProviders,
    }),
    [
      providers,
      selectedProvider,
      selectedModel,
      apiKeyStatus,
      saveApiKey,
      deleteApiKey,
      refreshProviders,
    ],
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider')
  return ctx
}
