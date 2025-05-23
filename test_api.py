#!/usr/bin/env python3
"""
Test script for the Audio Transcription API
"""
import requests
import json
import sys
from pathlib import Path
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE_URL = "https://localhost:4443"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", verify=False)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is it running?")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/", verify=False)
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Root endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        return False

def test_transcription_endpoint(audio_file_path=None):
    """Test the transcription endpoint"""
    print("\nTesting transcription endpoint...")
    
    if not audio_file_path:
        print("⚠️  No audio file provided, skipping transcription test")
        print("To test transcription, run: python test_api.py path/to/audio.webm")
        return True
    
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': f}
            print(f"Uploading {audio_path.name}...")
            response = requests.post(f"{API_BASE_URL}/transcribe", files=files, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription successful")
            print(f"File: {result['filename']}")
            print(f"Duration: {result['duration']:.2f} seconds")
            print(f"Transcription: {result['transcription'][:100]}...")
            return True
        else:
            print(f"❌ Transcription failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error: {error_detail}")
            except:
                print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during transcription test: {e}")
        return False

def test_docs_endpoint():
    """Test if docs are accessible"""
    print("\nTesting documentation endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", verify=False)
        if response.status_code == 200:
            print("✅ API documentation accessible at /docs")
            return True
        else:
            print(f"❌ Docs endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Audio Transcription API (HTTPS)")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_docs_endpoint,
    ]
    
    # Check if audio file is provided for transcription test
    audio_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run basic tests
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Run transcription test if audio file provided
    if test_transcription_endpoint(audio_file):
        passed += 1
    
    print("=" * 50)
    print(f"Tests completed: {passed}/{len(tests) + (1 if audio_file else 0)} passed")
    
    if passed == len(tests) + (1 if audio_file else 0):
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    
    print(f"\nAPI is running at: {API_BASE_URL}")
    print(f"Interactive docs: {API_BASE_URL}/docs")
    print("🔒 Using HTTPS with self-signed certificates")

if __name__ == "__main__":
    main() 