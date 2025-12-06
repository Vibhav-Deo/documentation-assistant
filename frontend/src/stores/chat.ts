import { create } from 'zustand'
import type { ChatMessage } from '@/types'

interface ChatState {
  messages: ChatMessage[]
  sessionId: string | null
  isLoading: boolean

  // Source filters
  filterConfluence: boolean
  filterJira: boolean
  filterGit: boolean
  filterCode: boolean

  // AI Settings
  model: string
  maxResults: number
  searchType: 'semantic' | 'hybrid' | 'keyword'

  // Actions
  addMessage: (message: ChatMessage) => void
  setMessages: (messages: ChatMessage[]) => void
  clearMessages: () => void
  setSessionId: (id: string) => void
  setLoading: (loading: boolean) => void
  setSourceFilter: (source: 'confluence' | 'jira' | 'git' | 'code', value: boolean) => void
  setModel: (model: string) => void
  setMaxResults: (max: number) => void
  setSearchType: (type: 'semantic' | 'hybrid' | 'keyword') => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: null,
  isLoading: false,

  // Source filters - all enabled by default
  filterConfluence: true,
  filterJira: true,
  filterGit: true,
  filterCode: true,

  // AI Settings - defaults
  model: 'mistral',
  maxResults: 5,
  searchType: 'semantic',

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setMessages: (messages) => set({ messages }),

  clearMessages: () => set({ messages: [], sessionId: null }),

  setSessionId: (id) => set({ sessionId: id }),

  setLoading: (loading) => set({ isLoading: loading }),

  setSourceFilter: (source, value) => {
    const filterMap = {
      confluence: 'filterConfluence',
      jira: 'filterJira',
      git: 'filterGit',
      code: 'filterCode',
    }
    set({ [filterMap[source]]: value })
  },

  setModel: (model) => set({ model }),

  setMaxResults: (max) => set({ maxResults: max }),

  setSearchType: (type) => set({ searchType: type }),
}))
