import { createContext, useContext, useState, useCallback } from 'react'
import { login as apiLogin } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const stored = localStorage.getItem('finca_user')
  const [user, setUser] = useState(stored ? JSON.parse(stored) : null)

  const login = useCallback(async (email, password) => {
    const { data } = await apiLogin(email, password)
    // data: { token, userId, email, nombreCompleto, rol, expiresAt }
    localStorage.setItem('finca_token', data.token)
    localStorage.setItem('finca_user', JSON.stringify(data))
    setUser(data)
    return data
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('finca_token')
    localStorage.removeItem('finca_user')
    setUser(null)
  }, [])

  const isAdmin  = user?.rol === 'Admin'
  const isCajero = user?.rol === 'Cajero'
  const isMesero = user?.rol === 'Mesero'

  return (
    <AuthContext.Provider value={{ user, login, logout, isAdmin, isCajero, isMesero }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
