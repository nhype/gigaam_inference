#!/bin/bash
set -e

echo "🎵 Audio Transcription Service (HTTPS)"
echo "======================================="
echo "Complete solution with React Frontend + FastAPI Backend"
echo "🔒 Secure HTTPS-only configuration"
echo ""

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose plugin is not available"
        echo "💡 Install Docker with Compose plugin or use legacy docker-compose"
        exit 1
    fi
}

# Function to build and start the service
start_service() {
    echo "🐳 Building and starting the audio transcription services..."
    docker compose up --build -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 15
    
    # Check if API service is healthy
    echo "🔍 Checking API service..."
    if curl -k -f https://localhost:4443/health &> /dev/null; then
        echo "✅ API service is running successfully!"
    else
        echo "❌ API service failed to start properly"
        docker compose logs audio-transcription-api
        exit 1
    fi
    
    # Check if frontend service is healthy
    echo "🔍 Checking frontend service..."
    if curl -k -f https://localhost:4446/ &> /dev/null; then
        echo "✅ Frontend service is running successfully!"
    else
        echo "❌ Frontend service failed to start properly"
        docker compose logs audio-transcription-frontend
        exit 1
    fi
    
    echo ""
    echo "🎉 Audio Transcription Service is ready!"
    echo ""
    echo "🌐 Access the service (HTTPS only):"
    echo "   🎤 Web Interface: https://localhost:4446"
    echo "   📱 Mobile-friendly and drag & drop ready!"
    echo "   🔒 Secure HTTPS connection"
    echo ""
    echo "🔧 API endpoints (HTTPS only):"
    echo "   📡 API Base: https://localhost:4443"
    echo "   ❤️  Health: https://localhost:4443/health"
    echo ""
    echo "📝 Testing options:"
    echo "   🌐 Use web interface: https://localhost:4446"
    echo "   🧪 Test API directly: python test_api.py [audio_file.webm]"
    echo "   📋 Example usage: python example_usage.py [audio_file.webm]"
    echo ""
    echo "📊 Management commands:"
    echo "   📋 View logs: docker compose logs -f"
    echo "   📋 API logs: docker compose logs -f audio-transcription-api"
    echo "   📋 Frontend logs: docker compose logs -f audio-transcription-frontend"
    echo "   🛑 Stop services: docker compose down"
    echo ""
    echo "⚠️  Note: Service uses HTTPS with self-signed certificates."
    echo "   Your browser may show a security warning - this is normal for development."
}

# Function to stop the service
stop_service() {
    echo "🛑 Stopping the audio transcription services..."
    docker compose down
    echo "✅ All services stopped"
}

# Function to show logs
show_logs() {
    echo "📋 Showing service logs..."
    if [ -n "$2" ]; then
        case "$2" in
            api|backend)
                docker compose logs -f audio-transcription-api
                ;;
            frontend|web)
                docker compose logs -f audio-transcription-frontend
                ;;
            *)
                echo "❌ Unknown service: $2"
                echo "Available services: api, frontend"
                exit 1
                ;;
        esac
    else
        docker compose logs -f
    fi
}

# Function to run tests
run_tests() {
    echo "🧪 Running API tests..."
    if [ -n "$1" ]; then
        python test_api.py "$1"
    else
        python test_api.py
    fi
}

# Function to check service status
check_status() {
    echo "🔍 Checking service status..."
    echo ""
    
    # Check if containers are running
    if docker compose ps | grep -q "audio-transcription"; then
        echo "📊 Container Status:"
        docker compose ps
        echo ""
        
        # Check API health
        echo "🔍 API Health Check:"
        if curl -k -s https://localhost:4443/health | jq . 2>/dev/null; then
            echo "✅ API is healthy"
        else
            echo "❌ API is not responding"
        fi
        echo ""
        
        # Check frontend
        echo "🔍 Frontend Health Check:"
        if curl -k -f https://localhost:4446/ &> /dev/null; then
            echo "✅ Frontend is accessible"
        else
            echo "❌ Frontend is not responding"
        fi
        echo ""
        echo "🔒 Services are running on HTTPS-only:"
        echo "   🎤 Frontend: https://localhost:4446"
        echo "   📡 API: https://localhost:4443"
    else
        echo "❌ No services are running"
        echo "💡 Start services with: $0 start"
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        check_docker
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        check_docker
        stop_service
        start_service
        ;;
    logs)
        show_logs "$@"
        ;;
    test)
        run_tests "$2"
        ;;
    build)
        check_docker
        echo "🔨 Building both services..."
        docker compose build
        echo "✅ Build complete"
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|test|build|status}"
        echo ""
        echo "Commands:"
        echo "  start     - Build and start both services (default)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  logs      - Show service logs (optionally specify 'api' or 'frontend')"
        echo "  test      - Run API tests (optionally with audio file)"
        echo "  build     - Build Docker images"
        echo "  status    - Check service status and health"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs api"
        echo "  $0 logs frontend" 
        echo "  $0 test audio.webm"
        echo "  $0 status"
        echo ""
        echo "🔒 HTTPS-only service configuration:"
        echo "  🎤 Frontend: https://localhost:4446"
        echo "  📡 API: https://localhost:4443"
        exit 1
        ;;
esac 