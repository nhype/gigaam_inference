#!/usr/bin/env python3
"""
Example usage of the Audio Transcription API

This script demonstrates how to use the API to transcribe audio files.
"""
import requests
import json
import time
from pathlib import Path
import sys

API_BASE_URL = "http://localhost:4444"

def check_api_status():
    """Check if the API is running and healthy"""
    print("🔍 Checking API status...")
    
    try:
        # Check health endpoint
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API is healthy")
            print(f"   Model: {health_data.get('model', 'unknown')}")
            print(f"   Model Status: {health_data.get('model_status', 'unknown')}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure the API is running with: ./start.sh")
        return False

def transcribe_file(file_path: str):
    """Transcribe an audio file using the API"""
    audio_path = Path(file_path)
    
    if not audio_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    print(f"\n🎵 Transcribing: {audio_path.name}")
    print(f"   File size: {audio_path.stat().st_size / 1024:.1f} KB")
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': (audio_path.name, f, 'audio/webm')}
            
            print("⏳ Uploading and processing...")
            start_time = time.time()
            
            response = requests.post(
                f"{API_BASE_URL}/transcribe",
                files=files,
                timeout=300  # 5 minute timeout
            )
            
            processing_time = time.time() - start_time
            
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Transcription completed!")
            print(f"   Processing time: {processing_time:.1f} seconds")
            print(f"   Audio duration: {result['duration']:.1f} seconds")
            print()
            print("📝 Transcription:")
            print("-" * 50)
            print(result['transcription'])
            print("-" * 50)
            
            return result
        else:
            print(f"❌ Transcription failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - the file might be too large or processing is taking too long")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def demonstrate_api():
    """Demonstrate API endpoints"""
    print("🚀 Audio Transcription API - Example Usage")
    print("=" * 60)
    
    # Check API status
    if not check_api_status():
        return
    
    print("\n📋 Available endpoints:")
    print(f"   • Root: {API_BASE_URL}/")
    print(f"   • Health: {API_BASE_URL}/health")
    print(f"   • Transcribe: {API_BASE_URL}/transcribe (POST)")
    print(f"   • Documentation: {API_BASE_URL}/docs")
    
    # Test root endpoint
    print("\n🏠 Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message', 'API responded')}")
        else:
            print(f"❌ Root endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Audio file provided as argument
        audio_file = sys.argv[1]
        
        # Check API first
        if not check_api_status():
            return
        
        # Transcribe the file
        result = transcribe_file(audio_file)
        
        if result:
            print("\n💾 Result summary:")
            print(f"   File: {result['filename']}")
            print(f"   Duration: {result['duration']:.1f}s")
            print(f"   Transcription length: {len(result['transcription'])} characters")
    else:
        # No file provided, just demonstrate the API
        demonstrate_api()
        
        print("\n💡 Usage:")
        print(f"   {sys.argv[0]} <audio_file.webm>")
        print("\n   Example:")
        print(f"   {sys.argv[0]} my_recording.webm")
        print("\n   To create a test WebM file, you can use FFmpeg:")
        print("   ffmpeg -f lavfi -i 'sine=frequency=1000:duration=5' -c:a libopus test.webm")

if __name__ == "__main__":
    main() 