from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import tempfile
import subprocess
import json
from typing import List
import asyncio
from pathlib import Path
import shutil
import gigaam

# Configuration
MAX_DURATION = 29  # Maximum duration per chunk in seconds
GIGAAM_MODEL = "v2_ctc"

# Global model instance
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model
    try:
        print(f"Loading Gigaam model: {GIGAAM_MODEL}")
        model = gigaam.load_model(GIGAAM_MODEL)
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e
    
    yield
    
    # Shutdown (if needed)
    # Clean up resources here if necessary
    pass

app = FastAPI(
    title="Audio Transcription API",
    description="API for transcribing audio files using Gigaam model",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None  # Disable the /docs endpoint
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Audio Transcription API", "status": "running"}

@app.get("/health")
async def health_check():
    global model
    model_status = "loaded" if model is not None else "not_loaded"
    return {"status": "healthy", "model": GIGAAM_MODEL, "model_status": model_status}

def get_audio_duration(file_path: str) -> float:
    """Get audio file duration in seconds using FFmpeg"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration_str = result.stdout.strip()
        
        # Handle cases where ffprobe returns 'N/A' or empty string
        if duration_str == 'N/A' or not duration_str:
            # Try alternative method to get duration
            cmd_alt = [
                "ffprobe", "-v", "quiet", "-show_entries", "stream=duration",
                "-of", "csv=p=0", file_path
            ]
            result_alt = subprocess.run(cmd_alt, capture_output=True, text=True, check=True)
            duration_str = result_alt.stdout.strip()
            
            # If still N/A, try using ffmpeg to get info
            if duration_str == 'N/A' or not duration_str:
                print(f"Warning: Could not get duration directly, using ffmpeg estimation")
                cmd_ffmpeg = [
                    "ffmpeg", "-i", file_path, "-f", "null", "-"
                ]
                result_ffmpeg = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)
                # Parse the duration from ffmpeg stderr output
                stderr = result_ffmpeg.stderr
                
                # Look for "Duration: HH:MM:SS.ss" pattern
                import re
                duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', stderr)
                if duration_match:
                    hours, minutes, seconds, centiseconds = duration_match.groups()
                    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
                    return float(total_seconds)
                else:
                    # If all methods fail, assume it's a short file
                    print(f"Warning: Could not determine duration, assuming 5 seconds")
                    return 5.0
        
        return float(duration_str)
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting audio duration: {e}")
        print(f"FFprobe output: {result.stdout if 'result' in locals() else 'N/A'}")
        # As fallback, assume it's a short file that can be transcribed directly
        print("Warning: Using fallback duration of 5 seconds")
        return 5.0

def split_audio(input_path: str, output_dir: str, segment_duration: int = MAX_DURATION) -> List[str]:
    """Split audio file into segments using FFmpeg"""
    try:
        output_pattern = os.path.join(output_dir, "segment_%03d.webm")
        cmd = [
            "ffmpeg", "-i", input_path,
            "-f", "segment",
            "-segment_time", str(segment_duration),
            "-c", "copy",
            "-reset_timestamps", "1",
            output_pattern
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Get list of created segments
        segments = []
        for file in sorted(os.listdir(output_dir)):
            if file.startswith("segment_") and file.endswith(".webm"):
                segments.append(os.path.join(output_dir, file))
        
        return segments
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error splitting audio: {str(e)}")

async def transcribe_with_gigaam(audio_path: str) -> str:
    """Transcribe audio file using Gigaam model"""
    global model
    
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Run transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        transcription = await loop.run_in_executor(
            None,
            model.transcribe,
            audio_path
        )
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file. If longer than 29 seconds, splits into chunks first.
    Returns only the full transcription text.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        if not file.filename or not file.filename.lower().endswith(".webm"):
            raise HTTPException(
                status_code=400, 
                detail="Only audio files (preferably WebM) are supported"
            )
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file
        input_path = os.path.join(temp_dir, "input.webm")
        try:
            with open(input_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"File saved to: {input_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
        
        try:
            # Get audio duration
            print(f"Getting duration for: {input_path}")
            duration = get_audio_duration(input_path)
            print(f"Audio duration: {duration} seconds")
            
            transcriptions = []
            
            if duration <= MAX_DURATION:
                # File is short enough, transcribe directly
                print("File is short, transcribing directly")
                transcription = await transcribe_with_gigaam(input_path)
                transcriptions.append(transcription)
            else:
                # Split file into segments
                print(f"File is long ({duration}s), splitting into segments")
                segments_dir = os.path.join(temp_dir, "segments")
                os.makedirs(segments_dir, exist_ok=True)
                
                segments = split_audio(input_path, segments_dir, MAX_DURATION)
                print(f"Created {len(segments)} segments")
                
                # Transcribe each segment
                for i, segment_path in enumerate(segments):
                    print(f"Transcribing segment {i+1}/{len(segments)}: {segment_path}")
                    transcription = await transcribe_with_gigaam(segment_path)
                    transcriptions.append(transcription)
            
            # Combine all transcriptions
            full_text = " ".join(transcriptions)
            print(f"Transcription completed. Length: {len(full_text)} characters")
            
            return JSONResponse(content={
                "filename": file.filename,
                "duration": duration,
                "transcription": full_text
            })
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            print(f"Detailed error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import ssl
    
    # Check if SSL certificates are available
    ssl_cert_path = os.environ.get('SSL_CERT_PATH', '/app/certs/fullchain.pem')
    ssl_key_path = os.environ.get('SSL_KEY_PATH', '/app/certs/privkey.pem')
    
    if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        print("SSL certificates found, starting HTTPS server on port 4443")
        
        # Start HTTPS server only
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=4443,
            ssl_certfile=ssl_cert_path,
            ssl_keyfile=ssl_key_path
        )
    else:
        print("ERROR: SSL certificates not found. HTTPS-only mode requires certificates.")
        print(f"Expected cert: {ssl_cert_path}")
        print(f"Expected key: {ssl_key_path}")
        raise FileNotFoundError("SSL certificates are required for HTTPS-only mode") 