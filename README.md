# Audio Transcription Service

A complete audio transcription solution with a FastAPI backend and React frontend. Upload audio files through a beautiful web interface and get instant transcriptions using the Gigaam model (v2_ctc).

## Features

### Backend API
- 🎵 Accept multiple audio formats (MP3, WAV, OGG, WebM, M4A, AAC)
- ⏱️ Automatic audio duration detection
- ✂️ Smart audio splitting for files > 29 seconds
- 🤖 Transcription using Gigaam v2_ctc model
- 🐳 Fully containerized with Docker
- 📝 Clean transcription results with full text
- 🏥 Health check endpoints
- 🔗 CORS-enabled for web frontend
- 🔒 SSL/HTTPS support with certificate management

### Frontend Web App
- 🎤 **Drag & Drop Upload**: Intuitive file upload interface
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🚀 **Real-time Processing**: Live progress indicators with retry logic
- 📋 **Copy Results**: One-click copy to clipboard
- ⚡ **Modern UI/UX**: Beautiful design with smooth animations
- 🔄 **Robust Error Handling**: User-friendly error messages with automatic retry
- 🔌 **Connection Resilience**: Automatic fallback from HTTPS to HTTP for development
- 📶 **API Status Indicator**: Real-time connection status display

## Production Setup (Current Deployment)

### Current Production URLs
- **Frontend**: https://195.35.3.51:4446
- **API Backend**: https://195.35.3.51:4443

### SSL Certificate Configuration
The service requires SSL certificates from `/root/n8n-certs/` for HTTPS support:
- Certificate: `cert.pem`
- Private Key: `private.pem`

**Important**: The API runs in HTTPS-only mode and will fail to start without valid SSL certificates.

## Quick Start

### Production Deployment (Current Setup)

```bash
# Current production configuration requires HTTPS with SSL certificates
docker compose up --build -d

# Access the web interface at https://your-domain:4446
```

### Development Setup

For local development, you'll need to either:
1. Provide SSL certificates in the expected location, or
2. Modify the `main.py` to support HTTP mode

```bash
# Start both services (API + Frontend)
docker compose up --build -d

# Access the web interface at https://localhost:4446 (with certs)
```

### Using the Web Interface

1. Open your deployment URL (https://195.35.3.51:4446 for production)
2. Check the API connection status indicator (should show ✅ API Connected)
3. Drag and drop an audio file or click to browse
4. Click "Transcribe Audio" 
5. Wait for processing (progress indicator shown, automatic retry if needed)
6. Copy or view your transcription results

### Advanced Connection Handling

The frontend includes robust connection management:
- **Automatic HTTPS/HTTP Fallback**: Tries HTTPS first, falls back to HTTP if SSL issues occur
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **Fresh Connections**: Forces new connections to avoid browser connection reuse issues
- **Real-time Status**: Shows connection status and provides meaningful error messages

## Services Overview

### Frontend (Port 4446 - Production / 4445 - Development)
- **Production URL**: https://195.35.3.51:4446
- **Technology**: React 18 + Nginx with SSL
- **Features**: File upload, drag & drop, transcription display, retry logic
- **Mobile-friendly**: Responsive design for all devices

### API Backend (Port 4443 - Production / 4444 - Development)  
- **Production URL**: https://195.35.3.51:4443
- **Technology**: FastAPI + Gigaam with SSL support
- **Features**: Audio processing and transcription with HTTPS/CORS

## API Endpoints

### `POST /transcribe`
Upload and transcribe an audio file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Audio file (preferably WebM format)

**Response:**
```json
{
  "filename": "audio.webm",
  "duration": 65.5,
  "transcription": "Complete transcribed text from the entire audio file"
}
```

**Error Responses:**
```json
{
  "detail": "Only audio files (preferably WebM) are supported"
}
```

**Processing Notes:**
- Files ≤ 29 seconds: Transcribed directly
- Files > 29 seconds: Split into chunks, transcribed separately, then combined into single text
- All processing is transparent to the user - you always get the full transcription
- Automatic retry logic handles temporary connection issues

### `GET /`
Root endpoint returning API status.

**Response:**
```json
{
  "message": "Audio Transcription API",
  "status": "running"
}
```

### `GET /health`
Health check endpoint with model loading status.

**Response:**
```json
{
  "status": "healthy",
  "model": "v2_ctc",
  "model_status": "loaded"
}
```

## Deployment Options

### Current Production Setup

The current deployment uses:
- **HTTPS**: SSL certificates from `/root/n8n-certs/`
- **Ports**: 4443 (API) and 4446 (Frontend)
- **Docker Compose**: Orchestrated deployment
- **Health Checks**: Automatic container health monitoring

### Using Docker Compose (Recommended)

```bash
# Build and start both services
docker compose up --build -d

# View logs for both services
docker compose logs -f

# View logs for specific service
docker compose logs -f audio-transcription-api
docker compose logs -f audio-transcription-frontend

# Stop all services
docker compose down

# Restart services
docker compose restart
```

### Individual Service Deployment

#### Frontend Only
```bash
cd frontend
docker build -t audio-transcription-frontend .
docker run -d -p 4446:443 --name frontend audio-transcription-frontend
```

#### API Only  
```bash
docker build -t audio-transcription-api .
docker run -d -p 4443:4443 --name api audio-transcription-api
```

## Configuration

### Current Configuration (Hardcoded)
The following values are currently hardcoded in `main.py`:
- `MAX_DURATION = 29` seconds (maximum chunk size for splitting)
- `GIGAAM_MODEL = "v2_ctc"` (default model)

Available Gigaam models:
- `v2_ctc` or `ctc` (default)
- `v2_rnnt` or `rnnt`
- `v1_ctc`
- `v1_rnnt`

**Note**: To change these values, you need to modify `main.py` directly. Environment variable support is not currently implemented.

## Audio Processing Details

1. **Input Validation**: Checks file type and format
2. **Duration Analysis**: Uses FFprobe to determine audio length
3. **Smart Splitting**: If > 29 seconds, splits using FFmpeg segment filter
4. **Model Loading**: Gigaam model loaded once at startup
5. **Transcription**: Each segment transcribed using Gigaam Python API
6. **Result Combination**: All segment transcriptions seamlessly combined into single text

## Supported Audio Formats

- **Primary**: WebM (recommended)
- **Secondary**: Any format supported by FFmpeg (MP3, WAV, M4A, FLAC, OGG, etc.)

## Requirements

- **Docker & Docker Compose**: For containerized deployment
- **Python 3.11+**: For local development
- **FFmpeg**: Audio processing (included in Docker image)
- **Gigaam**: Speech recognition model (auto-installed)
- **SSL Certificates**: Required for HTTPS mode

## Monitoring

The service includes comprehensive health checks:
- Container health check every 30 seconds
- `/health` endpoint with model loading status
- Automatic restart on failure
- Detailed logging for troubleshooting

## Project Structure

```
.
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Backend container definition
├── docker-compose.yml     # Service orchestration (API + Frontend)
├── start.sh               # Deployment script
├── .dockerignore          # Docker build optimization
├── package.json           # Node.js dependencies for tools
├── package-lock.json      # Node.js lock file
├── recorded-audio.webm    # Example audio file
├── frontend/              # React frontend application
│   ├── public/            # Static files
│   │   └── index.html     # HTML template
│   ├── src/               # React source code
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styling
│   │   └── index.js       # React entry point
│   ├── package.json       # Node.js dependencies
│   ├── Dockerfile         # Frontend container definition
│   ├── nginx.conf         # Nginx configuration
│   ├── .dockerignore      # Frontend build optimization
│   └── README.md          # Frontend documentation
└── README.md              # Project documentation
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Error**: Ensure SSL certificates are present in `/root/n8n-certs/`
   ```bash
   # Check if certificates exist
   ls -la /root/n8n-certs/
   ```

2. **FFmpeg not found**: Ensure FFmpeg is installed
   ```bash
   # Check if FFmpeg is available
   ffmpeg -version
   ```

3. **Gigaam model loading**: Check internet connection for initial model download
   ```bash
   # View model loading logs
   docker compose logs audio-transcription-api
   ```

4. **Large file processing**: Monitor memory usage for very long audio files
   ```bash
   # Check container resource usage
   docker stats audio-transcription-api
   ```

5. **Port already in use**: Change port in docker-compose.yml
   ```yaml
   ports:
     - "4445:4443"  # Change external port
   ```

### Debug Commands

```bash
# Check service status
curl https://localhost:4443/health

# View detailed logs
docker compose logs -f

# Check Docker containers
docker ps

# Restart service
docker compose restart
```

## Development

### Adding Features
1. Modify `main.py` for new endpoints
2. Update `requirements.txt` for new dependencies
3. Test locally with SSL certificates or modify for HTTP mode
4. Rebuild container: `docker compose up --build`

### Testing
- Health check: `curl https://localhost:4443/health`
- Upload test: Use the web interface at `https://localhost:4446`

## Performance Notes

- **Model Loading**: ~10-30 seconds on first startup (cached afterwards)
- **Transcription Speed**: Varies based on audio length and hardware
- **Memory Usage**: ~2-4GB for the model + processing overhead
- **Concurrent Requests**: Handled via FastAPI's async capabilities
- **Long Files**: Automatically chunked for optimal processing, results combined seamlessly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. The Gigaam model has its own licensing terms. 