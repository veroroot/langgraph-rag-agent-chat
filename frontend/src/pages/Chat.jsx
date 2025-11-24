import React, { useState, useEffect, useRef } from 'react'
import { chatAPI } from '../services/api'

const Chat = () => {
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [hoveredSessionId, setHoveredSessionId] = useState(null)
  const [editingSessionId, setEditingSessionId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [providers, setProviders] = useState({}) // { provider: [models] }
  const [selectedProvider, setSelectedProvider] = useState('')
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadSessions()
    loadProviders()
  }, [])

  useEffect(() => {
    // Update models when provider changes
    if (selectedProvider && providers[selectedProvider]) {
      const models = providers[selectedProvider]
      setAvailableModels(models)
      // Set default model to first available model for the provider
      if (models.length > 0) {
        setSelectedModel(models[0])
      }
    }
  }, [selectedProvider, providers])

  const loadProviders = async () => {
    try {
      const response = await chatAPI.getProviders()
      setProviders(response.data)
      // Set default provider to first available provider
      const providerNames = Object.keys(response.data)
      if (providerNames.length > 0 && !selectedProvider) {
        const firstProvider = providerNames[0]
        setSelectedProvider(firstProvider)
        const models = response.data[firstProvider]
        if (models && models.length > 0) {
          setSelectedModel(models[0])
        }
      }
    } catch (error) {
      console.error('Failed to load providers:', error)
    }
  }

  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId)
    }
  }, [currentSessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadSessions = async () => {
    try {
      const response = await chatAPI.getSessions()
      setSessions(response.data)
      if (response.data.length > 0 && !currentSessionId) {
        setCurrentSessionId(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const loadMessages = async (sessionId) => {
    try {
      const response = await chatAPI.getMessages(sessionId)
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = inputMessage
    setInputMessage('')
    setLoading(true)

    // Add user message to UI immediately
    const userMessageId = Date.now()
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage, id: userMessageId },
    ])

    // Add placeholder for assistant message
    const assistantMessageId = Date.now() + 1
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '', id: assistantMessageId, streaming: true },
    ])

    try {
      let streamedContent = ''
      let newSessionId = currentSessionId

      await chatAPI.sendMessageStream(
        userMessage,
        currentSessionId,
        selectedProvider || null,
        selectedModel || null,
        // onChunk
        (chunk) => {
          streamedContent += chunk
          // Update the assistant message in real-time
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: streamedContent }
                : msg
            )
          )
        },
        // onDone
        (sessionId) => {
          newSessionId = sessionId
          // Mark streaming as complete
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, streaming: false }
                : msg
            )
          )

          // Update current session if new session was created
          if (sessionId !== currentSessionId) {
            setCurrentSessionId(sessionId)
            loadSessions()
          }
          setLoading(false)
        },
        // onError
        (error) => {
          // Remove the placeholder message on error
          setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))
          alert('Failed to send message: ' + error)
          setLoading(false)
        }
      )
    } catch (error) {
      // Remove the placeholder message on error
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))
      alert('Failed to send message: ' + (error.response?.data?.detail || error.message))
      setLoading(false)
    }
  }

  const handleNewChat = async () => {
    try {
      setMessages([])
      setCurrentSessionId(null)
      
      // Create a new session
      const response = await chatAPI.createSession('New Chat')
      const newSessionId = response.data.id
      
      // Set the new session as current
      setCurrentSessionId(newSessionId)
      
      // Reload sessions to update the list
      await loadSessions()
    } catch (error) {
      console.error('Failed to create new session:', error)
      alert('Failed to create new chat: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation()
    
    const confirmed = window.confirm('삭제하시겠습니까?')
    if (!confirmed) return

    try {
      await chatAPI.deleteSession(sessionId)
      
      // If deleted session was current, clear it
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null)
        setMessages([])
      }
      
      // Reload sessions
      await loadSessions()
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('Failed to delete session: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleStartEdit = (session, e) => {
    e.stopPropagation()
    setEditingSessionId(session.id)
    setEditingTitle(session.title || `Chat ${session.id}`)
  }

  const handleSaveEdit = async (sessionId, e) => {
    e.stopPropagation()
    
    try {
      await chatAPI.updateSession(sessionId, editingTitle)
      setEditingSessionId(null)
      setEditingTitle('')
      await loadSessions()
    } catch (error) {
      console.error('Failed to update session:', error)
      alert('Failed to update session: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCancelEdit = (e) => {
    e.stopPropagation()
    setEditingSessionId(null)
    setEditingTitle('')
  }

  const handleKeyDown = (e, sessionId) => {
    if (e.key === 'Enter') {
      handleSaveEdit(sessionId, e)
    } else if (e.key === 'Escape') {
      handleCancelEdit(e)
    }
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 40px)' }}>
      <div
        style={{
          width: '250px',
          borderRight: '1px solid #ddd',
          padding: '10px',
          overflowY: 'auto',
        }}
      >
        <button
          onClick={handleNewChat}
          style={{
            width: '100%',
            padding: '10px',
            marginBottom: '10px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          New Chat
        </button>
        <div>
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => {
                if (editingSessionId !== session.id) {
                  setCurrentSessionId(session.id)
                }
              }}
              onMouseEnter={() => setHoveredSessionId(session.id)}
              onMouseLeave={() => setHoveredSessionId(null)}
              style={{
                padding: '10px',
                cursor: editingSessionId === session.id ? 'default' : 'pointer',
                backgroundColor:
                  currentSessionId === session.id ? '#f0f0f0' : 'transparent',
                marginBottom: '5px',
                borderRadius: '4px',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              {editingSessionId === session.id ? (
                <input
                  type="text"
                  value={editingTitle}
                  onChange={(e) => setEditingTitle(e.target.value)}
                  onKeyDown={(e) => handleKeyDown(e, session.id)}
                  onClick={(e) => e.stopPropagation()}
                  autoFocus
                  style={{
                    flex: 1,
                    padding: '5px',
                    fontSize: '14px',
                    border: '1px solid #007bff',
                    borderRadius: '4px',
                    outline: 'none',
                  }}
                />
              ) : (
                <span style={{ flex: 1 }}>
                  {session.title || `Chat ${session.id}`}
                </span>
              )}
              {(hoveredSessionId === session.id || editingSessionId === session.id) && (
                <div
                  style={{
                    display: 'flex',
                    gap: '5px',
                    alignItems: 'center',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {editingSessionId === session.id ? (
                    <>
                      <button
                        onClick={(e) => handleSaveEdit(session.id, e)}
                        style={{
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: '#28a745',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        ✓
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        style={{
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: '#6c757d',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        ✕
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={(e) => handleStartEdit(session, e)}
                        style={{
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: '#17a2b8',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                        title="Edit"
                      >
                        ✎
                      </button>
                      <button
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        style={{
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: '#dc3545',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                        title="Delete"
                      >
                        ✕
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px',
            backgroundColor: '#f9f9f9',
          }}
        >
          {messages.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                color: '#666',
                marginTop: '50px',
              }}
            >
              Start a conversation by typing a message below
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: '15px',
                  display: 'flex',
                  justifyContent:
                    msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  style={{
                    maxWidth: '70%',
                    padding: '10px 15px',
                    borderRadius: '10px',
                    backgroundColor:
                      msg.role === 'user' ? '#007bff' : '#e9e9e9',
                    color: msg.role === 'user' ? 'white' : 'black',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {msg.content}
                  {msg.streaming && (
                    <span
                      style={{
                        display: 'inline-block',
                        width: '8px',
                        height: '16px',
                        backgroundColor: '#666',
                        marginLeft: '4px',
                        animation: 'blink 1s infinite',
                      }}
                    />
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div
              style={{
                color: '#666',
                fontStyle: 'italic',
                padding: '10px 15px',
                marginBottom: '15px',
              }}
            >
              Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form
          onSubmit={handleSend}
          style={{
            padding: '20px',
            borderTop: '1px solid #ddd',
            backgroundColor: 'white',
          }}
        >
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              disabled={loading}
              style={{
                padding: '10px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: 'white',
                cursor: loading ? 'not-allowed' : 'pointer',
                minWidth: '120px',
                textTransform: 'capitalize',
              }}
            >
              {Object.keys(providers).map((provider) => (
                <option key={provider} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={loading || !selectedProvider}
              style={{
                padding: '10px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: 'white',
                cursor: loading || !selectedProvider ? 'not-allowed' : 'pointer',
                minWidth: '180px',
              }}
            >
              {availableModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
              style={{
                flex: 1,
                padding: '10px',
                fontSize: '16px',
                border: '1px solid #ddd',
                borderRadius: '4px',
              }}
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              style={{
                padding: '10px 20px',
                fontSize: '16px',
                backgroundColor: loading ? '#ccc' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Chat

