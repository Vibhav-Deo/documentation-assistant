import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Organization, AuthResponse } from '@/types'
import { authApi } from '@/lib/api/auth'
import { apiClient } from '@/lib/api'

interface AuthState {
  user: User | null
  organization: Organization | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string, organization: string) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      organization: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login(email, password)

          // Store token
          apiClient.setToken(response.access_token)

          // Store user info
          if (typeof window !== 'undefined') {
            localStorage.setItem('user_info', JSON.stringify(response))
          }

          set({
            user: response.user,
            organization: response.organization,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed'
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false
          })
          throw error
        }
      },

      register: async (email: string, password: string, name: string, organization: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.register(email, password, name, organization)

          // Store token
          apiClient.setToken(response.access_token)

          // Store user info
          if (typeof window !== 'undefined') {
            localStorage.setItem('user_info', JSON.stringify(response))
          }

          set({
            user: response.user,
            organization: response.organization,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Registration failed'
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false
          })
          throw error
        }
      },

      logout: () => {
        authApi.logout()
        set({
          user: null,
          organization: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },

      loadUser: async () => {
        const { token } = get()
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        set({ isLoading: true })
        try {
          const response = await authApi.getCurrentUser(token)
          set({
            user: response.user,
            organization: response.organization,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          // Token invalid, clear auth
          get().logout()
          set({ isLoading: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        organization: state.organization,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
