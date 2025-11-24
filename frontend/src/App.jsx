import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './components/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Upload from './pages/Upload'
import Documents from './pages/Documents'
import Chat from './pages/Chat'
import Layout from './components/Layout'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/chat" replace />} />
            <Route path="upload" element={<Upload />} />
            <Route path="documents" element={<Documents />} />
            <Route path="chat" element={<Chat />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App

