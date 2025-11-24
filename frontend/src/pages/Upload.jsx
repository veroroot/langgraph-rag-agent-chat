import React, { useState } from 'react'
import { uploadAPI } from '../services/api'

const Upload = () => {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setMessage('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setMessage('Please select a file')
      return
    }

    setUploading(true)
    setMessage('')

    try {
      await uploadAPI.upload(file)
      setMessage('File uploaded successfully!')
      setFile(null)
      e.target.reset()
    } catch (error) {
      setMessage(
        error.response?.data?.detail || 'Failed to upload file'
      )
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <h2>Upload Document</h2>
      <form onSubmit={handleSubmit} style={{ marginTop: '20px' }}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt,.md"
            style={{ marginBottom: '10px' }}
          />
          <p style={{ fontSize: '14px', color: '#666' }}>
            Supported formats: PDF, DOCX, TXT, MD
          </p>
        </div>
        {message && (
          <div
            style={{
              marginBottom: '15px',
              color: message.includes('success') ? 'green' : 'red',
            }}
          >
            {message}
          </div>
        )}
        <button
          type="submit"
          disabled={uploading || !file}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: uploading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: uploading ? 'not-allowed' : 'pointer',
          }}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  )
}

export default Upload

