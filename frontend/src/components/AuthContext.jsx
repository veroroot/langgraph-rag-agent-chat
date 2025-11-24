import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const response = await authAPI.getMe()
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password)
      const token = response.data.access_token
      localStorage.setItem('token', token)
      await checkAuth()
      return { success: true }
    } catch (error) {
      // Extract error message from various possible response formats
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.error_description ||
        error.response?.data?.message ||
        error.message ||
        '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.'
      return {
        success: false,
        error: errorMessage,
      }
    }
  }

  const register = async (email, password) => {
    try {
      await authAPI.register(email, password)
      return { success: true }
    } catch (error) {
      // Extract error message from various possible response formats
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.error_description ||
        error.response?.data?.message ||
        error.message ||
        '회원가입에 실패했습니다. 다시 시도해주세요.'
      return {
        success: false,
        error: errorMessage,
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

