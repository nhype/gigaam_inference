import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import './App.css';

// In Docker environment, the API will be accessible via the host using HTTPS
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'https://localhost:4443' 
  : `https://${window.location.hostname}:4443`;

// Fallback HTTP URL for development/testing
const API_BASE_URL_HTTP = window.location.hostname === 'localhost' 
  ? 'http://localhost:4444' 
  : `http://${window.location.hostname}:4444`;

// Configure axios with better connection handling
axios.defaults.timeout = 300000; // 5 minutes
axios.defaults.headers.common['Connection'] = 'close'; // Force close connections to avoid reuse issues

console.log('API Base URL (HTTPS):', API_BASE_URL);
console.log('API Base URL (HTTP fallback):', API_BASE_URL_HTTP);

function App() {
  const [file, setFile] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [fileInfo, setFileInfo] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking'); // 'checking', 'connected', 'error'
  const [retryCount, setRetryCount] = useState(0);

  // Helper function to create a fresh axios instance with no connection reuse
  const createFreshAxiosInstance = (baseURL) => {
    return axios.create({
      baseURL,
      timeout: 300000,
      headers: {
        'Connection': 'close', // Force new connection each time
        'Cache-Control': 'no-cache',
      },
      // Force HTTP/1.1 to avoid HTTP/2 connection issues with self-signed certs
      httpAgent: false,
      httpsAgent: false,
    });
  };

  // Enhanced retry function with exponential backoff
  const retryWithBackoff = async (fn, maxRetries = 3, baseDelay = 1000) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        console.log(`Attempt ${attempt} failed:`, error.message);
        
        // Don't retry on certain errors
        if (error.response?.status === 400 || error.response?.status === 413) {
          throw error;
        }
        
        if (attempt === maxRetries) {
          throw error;
        }
        
        // Wait with exponential backoff
        const delay = baseDelay * Math.pow(2, attempt - 1);
        console.log(`Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  };

  // Test API connectivity on component mount
  useEffect(() => {
    const checkApiHealth = async () => {
      setApiStatus('checking');
      
      try {
        console.log('Checking API health at:', `${API_BASE_URL}/health`);
        
        const healthCheck = async () => {
          const axiosInstance = createFreshAxiosInstance(API_BASE_URL);
          return await axiosInstance.get('/health', { timeout: 10000 });
        };
        
        const response = await retryWithBackoff(healthCheck, 2, 500);
        console.log('API health check successful:', response.data);
        setApiStatus('connected');
      } catch (err) {
        console.error('HTTPS API health check failed:', err);
        
        // Try HTTP fallback if HTTPS fails
        try {
          console.log('Trying HTTP fallback at:', `${API_BASE_URL_HTTP}/health`);
          
          const httpHealthCheck = async () => {
            const axiosInstance = createFreshAxiosInstance(API_BASE_URL_HTTP);
            return await axiosInstance.get('/health', { timeout: 10000 });
          };
          
          const response = await retryWithBackoff(httpHealthCheck, 2, 500);
          console.log('HTTP API health check successful:', response.data);
          setApiStatus('connected');
          // Update the API base URL to use HTTP
          window.API_BASE_URL_OVERRIDE = API_BASE_URL_HTTP;
        } catch (httpErr) {
          console.error('HTTP API health check also failed:', httpErr);
          setApiStatus('error');
        }
      }
    };

    checkApiHealth();
  }, []);

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
    setRetryCount(0);

    const formData = new FormData();
    formData.append('file', file);

    // Use override URL if available (from health check fallback)
    const apiUrl = window.API_BASE_URL_OVERRIDE || API_BASE_URL;
    
    console.log('Starting upload to:', `${apiUrl}/transcribe`);
    console.log('File info:', {
      name: file.name,
      size: file.size,
      type: file.type
    });

    const tryUpload = async (baseUrl) => {
      console.log(`Attempting upload to: ${baseUrl}/transcribe`);
      
      // Create fresh FormData for each attempt to avoid potential issues
      const freshFormData = new FormData();
      freshFormData.append('file', file);
      
      const axiosInstance = createFreshAxiosInstance(baseUrl);
      
      return await axiosInstance.post('/transcribe', freshFormData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout
        validateStatus: function (status) {
          return status >= 200 && status < 300;
        },
        // Additional options to prevent connection reuse issues
        maxRedirects: 0,
        // Force no caching
        transformRequest: [(data) => data] // Pass through unchanged
      });
    };

    try {
      let response;
      
      const uploadWithRetry = async (baseUrl) => {
        return await retryWithBackoff(
          () => tryUpload(baseUrl),
          3, // Max 3 retries
          1000 // Start with 1 second delay
        );
      };
      
      try {
        // Try primary URL (HTTPS or override from health check)
        console.log('Trying primary URL:', apiUrl);
        response = await uploadWithRetry(apiUrl);
      } catch (primaryErr) {
        console.error('Primary upload failed after retries:', primaryErr);
        
        // If primary was HTTPS and failed, try HTTP fallback
        if (apiUrl === API_BASE_URL && primaryErr.code !== 'ECONNABORTED') {
          console.log('Trying HTTP fallback for upload...');
          response = await uploadWithRetry(API_BASE_URL_HTTP);
          // Update override for future requests
          window.API_BASE_URL_OVERRIDE = API_BASE_URL_HTTP;
        } else {
          throw primaryErr;
        }
      }

      console.log('Upload successful:', response.data);
      setTranscription(response.data.transcription);
      setSuccess(true);
    } catch (err) {
      console.error('Upload error details:', {
        message: err.message,
        code: err.code,
        response: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText
      });

      let errorMessage = 'Failed to transcribe audio. Please try again.';

      if (err.response) {
        // Server responded with error status
        const status = err.response.status;
        const detail = err.response.data?.detail;
        
        if (status === 400) {
          errorMessage = `Invalid file: ${detail || 'Please check your audio file format'}`;
        } else if (status === 413) {
          errorMessage = 'File is too large. Please use a smaller audio file.';
        } else if (status === 500) {
          errorMessage = `Server error: ${detail || 'Internal server error occurred'}`;
        } else if (detail) {
          errorMessage = `Server error (${status}): ${detail}`;
        } else {
          errorMessage = `Server error: HTTP ${status} - ${err.response.statusText}`;
        }
      } else if (err.request) {
        // Network error - no response received
        if (err.code === 'ECONNABORTED') {
          errorMessage = 'Request timeout. The file might be too large or the server is busy.';
        } else if (err.code === 'ERR_NETWORK' || err.message.includes('ERR_SOCKET_NOT_CONNECTED')) {
          errorMessage = 'Connection failed. Retrying with a fresh connection... Please try again.';
        } else if (err.code === 'ERR_CERT_AUTHORITY_INVALID') {
          errorMessage = 'SSL certificate error. The connection is not secure.';
        } else {
          errorMessage = `Network error: ${err.message}. Please try again in a moment.`;
        }
      } else {
        // Something else happened
        errorMessage = `Error: ${err.message}`;
      }

      setError(errorMessage);
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
          <div className="api-status">
            {apiStatus === 'checking' && (
              <span className="status-indicator checking">🔄 Checking API connection...</span>
            )}
            {apiStatus === 'connected' && (
              <span className="status-indicator connected">✅ API Connected</span>
            )}
            {apiStatus === 'error' && (
              <span className="status-indicator error">❌ API Connection Failed</span>
            )}
          </div>
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