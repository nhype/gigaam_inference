# Audio Transcription API

A FastAPI-based service that transcribes audio files using the Gigaam model (v2_ctc). The service automatically splits audio files longer than 29 seconds into smaller chunks for optimal processing and returns the complete transcription.

## Features

- 🎵 Accept WebM audio files via HTTP upload
- ⏱️ Automatic audio duration detection
- ✂️ Smart audio splitting for files > 29 seconds
- 🤖 Transcription using Gigaam v2_ctc model
- 🐳 Fully containerized with Docker
- 📝 Clean transcription results with full text
- 🏥 Health check endpoints
- 🚀 Easy deployment with included scripts

## Quick Start

### One-Command Setup

```bash
# Start the service (builds and runs everything)
./start.sh

# The API will be available at http://localhost:4444
```

### Testing the API

```bash
# Test without audio file (basic endpoints)
python test_api.py

# Test with audio file
python test_api.py path/to/audio.webm

# Run example usage
python example_usage.py path/to/audio.webm
```

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

### Using the Start Script (Recommended)

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

### Using Docker Compose

```bash
# Build and start
docker compose up --build -d

# Stop
docker compose down

# View logs
docker compose logs -f
```

### Using Docker

```bash
# Build the image
docker build -t audio-transcription-api .

# Run the container
docker run -d -p 4444:4444 --name audio-transcription-api audio-transcription-api
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure FFmpeg is installed
# For Ubuntu/Debian: sudo apt-get install ffmpeg
# For macOS: brew install ffmpeg

# Run the application
python main.py
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
├── Dockerfile             # Container definition
├── docker-compose.yml     # Service orchestration
├── start.sh               # Deployment script
├── test_api.py            # API testing script
├── example_usage.py       # Usage examples
├── .dockerignore          # Docker build optimization
└── README.md              # Documentation
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