import { createContext, useContext, useState } from 'react'
import {
  getToken,
  clearToken,
  login as apiLogin,
  register as apiRegister,
} from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setTok] = useState(getToken())

  async function login(email, password) {
    const data = await apiLogin(email, password)
    setTok(data.access_token)
  }

  async function register(email, password) {
    await apiRegister(email, password)
    await login(email, password) // auto-login after registering
  }

  function logout() {
    clearToken()
    setTok(null)
  }

  const value = { token, isAuthenticated: !!token, login, register, logout }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
