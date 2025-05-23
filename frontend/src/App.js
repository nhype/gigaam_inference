import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import './App.css';

// In Docker environment, the API will be accessible via the host using HTTPS
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'https://localhost:4443' 
  : `https://${window.location.hostname}:4443`;

function App() {
  const [file, setFile] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [fileInfo, setFileInfo] = useState(null);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      setError('Please upload only audio files (MP3, WAV, OGG, WebM)');
      return;
    }

    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      setFile(selectedFile);
      setError('');
      setSuccess(false);
      setTranscription('');
      setFileInfo({
        name: selectedFile.name,
        size: (selectedFile.size / (1024 * 1024)).toFixed(2), // Size in MB
        type: selectedFile.type
      });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.ogg', '.webm', '.m4a', '.aac']
    },
    multiple: false,
    maxSize: 100 * 1024 * 1024 // 100MB
  });

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess(false);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/transcribe`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout
      });

      setTranscription(response.data.transcription);
      setSuccess(true);
    } catch (err) {
      console.error('Error uploading file:', err);
      if (err.response?.data?.detail) {
        setError(`Server error: ${err.response.data.detail}`);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timeout. The file might be too large or the server is busy.');
      } else {
        setError('Failed to transcribe audio. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setTranscription('');
    setError('');
    setSuccess(false);
    setFileInfo(null);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(transcription);
    // You could add a toast notification here
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🎵 Audio Transcription Service</h1>
          <p>Upload your audio files and get instant transcriptions</p>
        </header>

        <div className="upload-section">
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
          >
            <input {...getInputProps()} />
            {file ? (
              <div className="file-preview">
                <div className="file-icon">📁</div>
                <div className="file-details">
                  <h3>{fileInfo.name}</h3>
                  <p>{fileInfo.size} MB • {fileInfo.type}</p>
                </div>
                <button onClick={(e) => { e.stopPropagation(); resetForm(); }} className="remove-btn">
                  ✕
                </button>
              </div>
            ) : (
              <div className="dropzone-content">
                <div className="upload-icon">🎤</div>
                <h3>Drop your audio file here</h3>
                <p>or click to browse</p>
                <div className="supported-formats">
                  <span>Supported: MP3, WAV, OGG, WebM</span>
                </div>
              </div>
            )}
          </div>

          {file && (
            <button
              onClick={handleUpload}
              disabled={loading}
              className={`upload-btn ${loading ? 'loading' : ''}`}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Transcribing...
                </>
              ) : (
                'Transcribe Audio'
              )}
            </button>
          )}
        </div>

        {error && (
          <div className="message error">
            <span className="message-icon">⚠️</span>
            {error}
          </div>
        )}

        {success && transcription && (
          <div className="results-section">
            <div className="message success">
              <span className="message-icon">✅</span>
              Transcription completed successfully!
            </div>
            
            <div className="transcription-container">
              <div className="transcription-header">
                <h3>Transcription</h3>
                <button onClick={copyToClipboard} className="copy-btn">
                  📋 Copy
                </button>
              </div>
              <div className="transcription-text">
                {transcription}
              </div>
            </div>
          </div>
        )}

        <footer className="footer">
          <p>Powered by Gigaam Speech Recognition</p>
        </footer>
      </div>
    </div>
  );
}

export default App; 