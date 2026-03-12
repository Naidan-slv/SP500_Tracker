import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { fetchMe, loginUser, registerUser, verifyEmailToken } from '../lib/api'
import type { LoginResponse, RegisterResponse, UserPublic } from '../lib/types'

type AuthContextValue = {
  user: UserPublic | null
  token: string | null
  sessionLoading: boolean
  login: (email: string, password: string) => Promise<LoginResponse>
  register: (email: string, password: string) => Promise<RegisterResponse>
  verifyEmail: (token: string) => Promise<string>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)
const TOKEN_KEY = 'sp500_tracker_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [sessionLoading, setSessionLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function loadSession() {
      if (!token) {
        if (!cancelled) {
          setUser(null)
          setSessionLoading(false)
        }
        return
      }

      try {
        const me = await fetchMe(token)
        if (!cancelled) {
          setUser(me)
        }
      } catch {
        if (!cancelled) {
          localStorage.removeItem(TOKEN_KEY)
          setToken(null)
          setUser(null)
        }
      } finally {
        if (!cancelled) {
          setSessionLoading(false)
        }
      }
    }

    void loadSession()
    return () => {
      cancelled = true
    }
  }, [token])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      sessionLoading,
      login: async (email: string, password: string) => {
        const response = await loginUser(email, password)
        localStorage.setItem(TOKEN_KEY, response.access_token)
        setToken(response.access_token)
        setUser(response.user)
        return response
      },
      register: async (email: string, password: string) => {
        return registerUser(email, password)
      },
      verifyEmail: async (verificationToken: string) => {
        const response = await verifyEmailToken(verificationToken)
        return response.message
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUser(null)
      },
    }),
    [sessionLoading, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
