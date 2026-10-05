import React, { createContext, useState, useEffect } from 'react'
import { authAPI, tokenStore } from '../services/api'
import toast from 'react-hot-toast'

export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await authAPI.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const acceptSession = (data) => {
    tokenStore.set(data.token)
    const { token, ...profile } = data
    setUser(profile)
    return profile
  }

  const login = async (credentials) => {
    const response = await authAPI.login(credentials)
    toast.success('Welcome back!')
    return acceptSession(response.data)
  }

  const register = async (userData) => {
    const response = await authAPI.register(userData)
    toast.success('Account created successfully!')
    return acceptSession(response.data)
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
    tokenStore.set(null)
    setUser(null)
    toast.success('Logged out successfully')
  }

  return (
    <AuthContext.Provider value={{ user, setUser, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}
