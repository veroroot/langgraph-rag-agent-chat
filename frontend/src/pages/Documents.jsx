import React, { useState, useEffect } from 'react'
import { documentsAPI } from '../services/api'

const Documents = () => {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const response = await documentsAPI.getAll()
      setDocuments(response.data)
    } catch (err) {
      setError('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      await documentsAPI.delete(id)
      loadDocuments()
    } catch (err) {
      alert('Failed to delete document')
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h2>Documents</h2>
      {error && <div style={{ color: 'red', marginTop: '10px' }}>{error}</div>}
      {documents.length === 0 ? (
        <p style={{ marginTop: '20px' }}>No documents uploaded yet.</p>
      ) : (
        <table
          style={{
            width: '100%',
            marginTop: '20px',
            borderCollapse: 'collapse',
          }}
        >
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '10px', textAlign: 'left' }}>Filename</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Status</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Uploaded</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '10px' }}>{doc.filename}</td>
                <td style={{ padding: '10px' }}>{doc.status}</td>
                <td style={{ padding: '10px' }}>
                  {formatDate(doc.uploaded_at)}
                </td>
                <td style={{ padding: '10px' }}>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    style={{
                      padding: '5px 10px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default Documents

