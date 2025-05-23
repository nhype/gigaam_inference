#!/bin/bash
set -e

echo "🎵 Audio Transcription API with Gigaam"
echo "======================================"

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
    echo "🐳 Building and starting the audio transcription service..."
    docker compose up --build -d
    
    echo "⏳ Waiting for service to be ready..."
    sleep 10
    
    # Check if service is healthy
    if curl -f http://localhost:4444/health &> /dev/null; then
        echo "✅ Service is running successfully!"
        echo ""
        echo "🌐 API endpoints:"
        echo "   - API: http://localhost:4444"
        echo "   - Health: http://localhost:4444/health"
        echo "   - Docs: http://localhost:4444/docs"
        echo ""
        echo "📝 To test the API:"
        echo "   python test_api.py [audio_file.webm]"
        echo ""
        echo "📋 To view logs:"
        echo "   docker compose logs -f"
        echo ""
        echo "🛑 To stop the service:"
        echo "   docker compose down"
    else
        echo "❌ Service failed to start properly. Check logs:"
        docker compose logs
        exit 1
    fi
}

# Function to stop the service
stop_service() {
    echo "🛑 Stopping the audio transcription service..."
    docker compose down
    echo "✅ Service stopped"
}

# Function to show logs
show_logs() {
    echo "📋 Showing service logs..."
    docker compose logs -f
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
        show_logs
        ;;
    test)
        run_tests "$2"
        ;;
    build)
        check_docker
        echo "🔨 Building the service..."
        docker compose build
        echo "✅ Build complete"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|test|build}"
        echo ""
        echo "Commands:"
        echo "  start     - Build and start the service (default)"
        echo "  stop      - Stop the service"
        echo "  restart   - Restart the service"
        echo "  logs      - Show service logs"
        echo "  test      - Run API tests (optionally with audio file)"
        echo "  build     - Build the Docker image"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 test audio.webm"
        echo "  $0 logs"
        exit 1
        ;;
esac 