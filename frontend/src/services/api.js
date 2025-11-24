import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect on login/register endpoints - let them handle errors
      const url = error.config?.url || ''
      const isAuthEndpoint = url.includes('/api/v1/auth/login') || url.includes('/api/v1/auth/register')
      
      if (!isAuthEndpoint) {
        localStorage.removeItem('token')
        // Only redirect if not already on login/register page
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: (email, password) =>
    api.post('/api/v1/auth/register', { email, password }),
  login: (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    return api.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getMe: () => api.get('/api/v1/auth/me'),
}

// Upload API
export const uploadAPI = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/v1/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// Documents API
export const documentsAPI = {
  getAll: (skip = 0, limit = 100) =>
    api.get('/api/v1/docs/', { params: { skip, limit } }),
  getOne: (id) => api.get(`/api/v1/docs/${id}`),
  update: (id, data) => api.patch(`/api/v1/docs/${id}`, data),
  delete: (id) => api.delete(`/api/v1/docs/${id}`),
}

// Chat API
export const chatAPI = {
  getProviders: () => api.get('/api/v1/chat/providers'),
  createSession: (title) => api.post('/api/v1/chat/sessions', { title }),
  getSessions: (skip = 0, limit = 100) =>
    api.get('/api/v1/chat/sessions', { params: { skip, limit } }),
  getMessages: (sessionId) =>
    api.get(`/api/v1/chat/sessions/${sessionId}/messages`),
  sendMessage: (message, sessionId = null, provider = null, model = null) =>
    api.post('/api/v1/chat/', { message, session_id: sessionId, stream: false, provider, model }),
  sendMessageStream: async (message, sessionId, provider, model, onChunk, onDone, onError) => {
    const token = localStorage.getItem('token')
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ message, session_id: sessionId, provider, model }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Network error' }))
      onError?.(error.detail || 'Failed to send message')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'session') {
                // Session info received
              } else if (data.type === 'chunk') {
                onChunk?.(data.content)
              } else if (data.type === 'done') {
                onDone?.(data.session_id)
                return
              } else if (data.type === 'error') {
                onError?.(data.error)
                return
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      onError?.(error.message || 'Stream error')
    }
  },
  updateSession: (sessionId, title) =>
    api.patch(`/api/v1/chat/sessions/${sessionId}`, { title }),
  deleteSession: (sessionId) =>
    api.delete(`/api/v1/chat/sessions/${sessionId}`),
}

export default api

