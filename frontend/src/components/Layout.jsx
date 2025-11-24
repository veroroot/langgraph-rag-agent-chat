import React from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

const Layout = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: '200px',
          backgroundColor: '#f5f5f5',
          padding: '20px',
          borderRight: '1px solid #ddd',
        }}
      >
        <h2 style={{ marginBottom: '20px' }}>RAG Agent</h2>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <Link to="/chat" style={{ textDecoration: 'none', color: '#333' }}>
            Chat
          </Link>
          <Link to="/upload" style={{ textDecoration: 'none', color: '#333' }}>
            Upload
          </Link>
          <Link to="/documents" style={{ textDecoration: 'none', color: '#333' }}>
            Documents
          </Link>
        </nav>
        <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
          <p style={{ fontSize: '14px', marginBottom: '10px' }}>
            {user?.email}
          </p>
          <button onClick={handleLogout} style={{ width: '100%' }}>
            Logout
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: '20px' }}>
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

