import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, register as apiRegister, deleteAccount as apiDelete } from '../api.js'

const Ctx = createContext(null)

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 이전 버전 'solace_*' 키 → 'inner_gallery_*' 마이그레이션
    const oldToken = localStorage.getItem('solace_token')
    const oldUser  = localStorage.getItem('solace_user')
    if (oldToken && !localStorage.getItem('inner_gallery_token')) {
      localStorage.setItem('inner_gallery_token', oldToken)
      localStorage.removeItem('solace_token')
    }
    if (oldUser && !localStorage.getItem('inner_gallery_user')) {
      localStorage.setItem('inner_gallery_user', oldUser)
      localStorage.removeItem('solace_user')
    }

    const stored = localStorage.getItem('inner_gallery_user')
    const token  = localStorage.getItem('inner_gallery_token')
    if (stored && token) {
      try { setUser(JSON.parse(stored)) } catch {}
    }
    setLoading(false)

    const handleExpired = () => setUser(null)
    window.addEventListener('auth:expired', handleExpired)
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [])

  const login = async ({ username, password }) => {
    const data = await apiLogin({ username, password })
    localStorage.setItem('inner_gallery_token', data.access_token)
    localStorage.setItem('inner_gallery_user', JSON.stringify({ id: data.user_id, username: data.username }))
    setUser({ id: data.user_id, username: data.username })
  }

  const register = async ({ username, email, password }) => {
    await apiRegister({ username, email, password })
  }

  const logout = () => {
    localStorage.removeItem('inner_gallery_token')
    localStorage.removeItem('inner_gallery_user')
    setUser(null)
  }

  const deleteAccount = async () => {
    await apiDelete()
    logout()
  }

  return (
    <Ctx.Provider value={{ user, loading, login, logout, register, deleteAccount }}>
      {children}
    </Ctx.Provider>
  )
}

export const useAuth = () => useContext(Ctx)
