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

### Frontend Web App
- 🎤 **Drag & Drop Upload**: Intuitive file upload interface
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🚀 **Real-time Processing**: Live progress indicators
- 📋 **Copy Results**: One-click copy to clipboard
- ⚡ **Modern UI/UX**: Beautiful design with smooth animations
- 🔄 **Auto Error Handling**: User-friendly error messages

## Quick Start

### One-Command Setup

```bash
# Start both services (API + Frontend)
docker compose up --build -d

# Access the web interface at http://localhost:4445
# API documentation at http://localhost:4444/docs
```

### Using the Web Interface

1. Open http://localhost:4445 in your browser
2. Drag and drop an audio file or click to browse
3. Click "Transcribe Audio" 
4. Wait for processing (progress indicator shown)
5. Copy or view your transcription results

### Testing the API Directly

```bash
# Test basic endpoints
python test_api.py

# Test with audio file
python test_api.py path/to/audio.webm

# Run example usage
python example_usage.py path/to/audio.webm
```

## Services Overview

### Frontend (Port 4445)
- **URL**: http://localhost:4445
- **Technology**: React 18 + Nginx
- **Features**: File upload, drag & drop, transcription display
- **Mobile-friendly**: Responsive design for all devices

### API Backend (Port 4444)  
- **URL**: http://localhost:4444
- **Documentation**: http://localhost:4444/docs
- **Technology**: FastAPI + Gigaam
- **Features**: Audio processing and transcription

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

**Processing Notes:**
- Files ≤ 29 seconds: Transcribed directly
- Files > 29 seconds: Split into chunks, transcribed separately, then combined into single text
- All processing is transparent to the user - you always get the full transcription

### `GET /`
Root endpoint returning API status.

### `GET /health`
Health check endpoint with model loading status.

### `GET /docs`
Interactive API documentation (Swagger UI).

## Deployment Options

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
docker run -d -p 4445:80 --name frontend audio-transcription-frontend
```

#### API Only  
```bash
docker build -t audio-transcription-api .
docker run -d -p 4444:4444 --name api audio-transcription-api
```

### Using the Start Script

```bash
# Start the service
./start.sh start

# View logs
./start.sh logs

# Stop the service
./start.sh stop

# Run tests
./start.sh test [audio_file.webm]

# Build only
./start.sh build
```

### Local Development

#### Frontend Development
```bash
cd frontend
npm install
npm start
# Available at http://localhost:3000
```

#### API Development
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure FFmpeg is installed
# For Ubuntu/Debian: sudo apt-get install ffmpeg
# For macOS: brew install ffmpeg

# Run the application
python main.py
# Available at http://localhost:4444
```

## Usage Examples

### Using curl
```bash
# Upload and transcribe an audio file
curl -X POST "http://localhost:4444/transcribe" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@audio.webm"
```

### Using Python requests
```python
import requests

with open('audio.webm', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:4444/transcribe', files=files)
    result = response.json()
    print(result['transcription'])
```

### Using JavaScript/fetch
```javascript
const formData = new FormData();
formData.append('file', audioFile);

fetch('http://localhost:4444/transcribe', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data.transcription));
```

## Configuration

### Environment Variables
You can override configuration in docker-compose.yml:
```yaml
environment:
  - MAX_DURATION=30
  - GIGAAM_MODEL=v2_ctc
```

Available Gigaam models:
- `v2_ctc` or `ctc` (default)
- `v2_rnnt` or `rnnt`
- `v1_ctc`
- `v1_rnnt`

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
├── test_api.py            # API testing script
├── example_usage.py       # Usage examples
├── .dockerignore          # Docker build optimization
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

1. **FFmpeg not found**: Ensure FFmpeg is installed
   ```bash
   # Check if FFmpeg is available
   ffmpeg -version
   ```

2. **Gigaam model loading**: Check internet connection for initial model download
   ```bash
   # View model loading logs
   ./start.sh logs
   ```

3. **Large file processing**: Monitor memory usage for very long audio files
   ```bash
   # Check container resource usage
   docker stats audio-transcription-api
   ```

4. **Port already in use**: Change port in docker-compose.yml
   ```yaml
   ports:
     - "4445:4444"  # Change external port
   ```

### Debug Commands

```bash
# Check service status
curl http://localhost:4444/health

# View detailed logs
./start.sh logs

# Test API endpoints
python test_api.py

# Check Docker containers
docker ps

# Restart service
./start.sh restart
```

## Development

### Adding Features
1. Modify `main.py` for new endpoints
2. Update `requirements.txt` for new dependencies
3. Test locally: `python main.py`
4. Rebuild container: `./start.sh build`

### Testing
- Basic API tests: `python test_api.py`
- With audio file: `python test_api.py audio.webm`
- Example usage: `python example_usage.py audio.webm`

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