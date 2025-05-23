# Audio Transcription Frontend

A modern React-based web interface for the Audio Transcription Service. Upload audio files and get instant transcriptions using advanced speech recognition technology.

## Features

- 🎤 **Drag & Drop Upload**: Simply drag audio files onto the interface or click to browse
- 📁 **Multiple Format Support**: Supports MP3, WAV, OGG, WebM, M4A, and AAC files
- 🚀 **Real-time Processing**: Get transcriptions with live progress indicators
- 📱 **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- 📋 **Copy to Clipboard**: Easily copy transcription results
- ⚡ **Modern UI/UX**: Beautiful, intuitive interface with smooth animations

## Supported Audio Formats

- MP3
- WAV
- OGG
- WebM
- M4A
- AAC

## File Size Limit

- Maximum file size: 100MB
- Files longer than 29 seconds are automatically chunked for optimal processing

## Technology Stack

- **React 18**: Modern React with hooks
- **React Dropzone**: Drag and drop file upload
- **Axios**: HTTP client for API communication
- **CSS3**: Modern styling with gradients and animations
- **Nginx**: Production web server

## Development

To run locally:

```bash
npm install
npm start
```

The application will be available at `http://localhost:3000`.

## Docker

The frontend is containerized and served by Nginx in production:

```bash
docker build -t audio-transcription-frontend .
docker run -p 4445:80 audio-transcription-frontend
```

## API Integration

The frontend communicates with the Audio Transcription API running on port 4444. It automatically detects the environment and adjusts the API URL accordingly.

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

Modern browsers with ES6+ support are required. 