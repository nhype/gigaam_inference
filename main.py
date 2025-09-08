from fastapi import FastAPI, File, UploadFile, HTTPException, Request
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
import logging
import traceback
from datetime import datetime

# Configuration
MAX_DURATION = 20  # Maximum duration per chunk in seconds
GIGAAM_MODEL = "v2_ctc"

# Concurrency settings
MAX_CONCURRENT_TRANSCRIPTIONS = 4  # Limit concurrent transcription tasks
TRANSCRIPTION_SEMAPHORE = None  # Will be initialized in lifespan

# Service configuration
FAIL_WITHOUT_MODEL = os.environ.get('FAIL_WITHOUT_MODEL', 'true').lower() == 'true'

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/transcription_app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Suppress PyTorch security warning for trusted model loading
import warnings
warnings.filterwarnings("ignore", message=".*torch.load.*weights_only.*", category=FutureWarning)

# Global model instance
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model, TRANSCRIPTION_SEMAPHORE
    try:
        logger.info(f"Loading Gigaam model: {GIGAAM_MODEL}")
        model = gigaam.load_model(GIGAAM_MODEL)
        logger.info("Model loaded successfully")

        # Initialize semaphore for limiting concurrent transcriptions
        TRANSCRIPTION_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_TRANSCRIPTIONS)
        logger.info(f"Initialized semaphore with {MAX_CONCURRENT_TRANSCRIPTIONS} concurrent transcription slots")
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
        if FAIL_WITHOUT_MODEL:
            logger.error("FAIL_WITHOUT_MODEL is enabled - exiting application")
            raise RuntimeError(f"Failed to load transcription model: {e}")
        else:
            logger.warning("Continuing without model - transcription will fail but service will be available")
            model = None
            # Still initialize semaphore for when model is available
            TRANSCRIPTION_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_TRANSCRIPTIONS)

    yield

    # Shutdown (if needed)
    # Clean up resources here if necessary
    logger.info("Application shutdown initiated")
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
    if model is None:
        return JSONResponse(
            status_code=503,  # Service Unavailable
            content={"status": "unhealthy", "model": GIGAAM_MODEL, "model_status": "not_loaded", "error": "Transcription model not available"}
        )
    return {"status": "healthy", "model": GIGAAM_MODEL, "model_status": "loaded"}

def get_audio_duration(file_path: str) -> float:
    """Get audio file duration in seconds using FFmpeg"""
    import re

    logger.debug(f"Getting audio duration for: {file_path}")
    try:
        # Method 1: Try format duration first
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration_str = result.stdout.strip()
        
        # Check if we got a valid duration
        if duration_str and duration_str != 'N/A':
            try:
                duration = float(duration_str)
                if duration > 0:
                    return duration
            except ValueError:
                pass
        
        # Method 2: Try stream duration
        cmd_alt = [
            "ffprobe", "-v", "quiet", "-show_entries", "stream=duration",
            "-of", "csv=p=0", file_path
        ]
        result_alt = subprocess.run(cmd_alt, capture_output=True, text=True, check=True)
        
        # Process all stream durations and take the maximum valid one
        for line in result_alt.stdout.strip().split('\n'):
            if line and line != 'N/A':
                try:
                    duration = float(line)
                    if duration > 0:
                        return duration
                except ValueError:
                    continue
        
        # Method 3: Use ffprobe with JSON output for more reliable parsing
        cmd_json = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path
        ]
        result_json = subprocess.run(cmd_json, capture_output=True, text=True, check=True)
        
        import json
        try:
            data = json.loads(result_json.stdout)
            
            # Try format duration
            if 'format' in data and 'duration' in data['format']:
                duration = float(data['format']['duration'])
                if duration > 0:
                    return duration
            
            # Try stream durations
            if 'streams' in data:
                for stream in data['streams']:
                    if 'duration' in stream:
                        try:
                            duration = float(stream['duration'])
                            if duration > 0:
                                return duration
                        except (ValueError, TypeError):
                            continue
        except json.JSONDecodeError:
            pass
        
        # Method 4: Parse ffmpeg stderr output as last resort
        logger.warning(f"Could not get duration directly, using ffmpeg stderr parsing for {file_path}")
        cmd_ffmpeg = [
            "ffmpeg", "-i", file_path, "-f", "null", "-"
        ]
        result_ffmpeg = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)
        stderr = result_ffmpeg.stderr
        
        # Look for "Duration: HH:MM:SS.ss" pattern in metadata
        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', stderr)
        if duration_match:
            hours, minutes, seconds, centiseconds = duration_match.groups()
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
            if total_seconds > 0:
                return float(total_seconds)
        
        # For WebM files without duration metadata, look for the final time in progress output
        # This appears as "time=HH:MM:SS.ss" in the last line before completion
        time_matches = re.findall(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', stderr)
        if time_matches:
            # Get the last time value (final duration)
            last_time = time_matches[-1]
            hours, minutes, seconds = last_time
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            if total_seconds > 0:
                logger.info(f"Duration found from ffmpeg progress: {total_seconds} seconds for {file_path}")
                return float(total_seconds)
        
        # Method 5: Use ffmpeg with more verbose output to get duration
        logger.warning(f"Trying verbose ffmpeg parsing for {file_path}")
        cmd_verbose = [
            "ffmpeg", "-i", file_path, "-hide_banner", "-f", "null", "-"
        ]
        result_verbose = subprocess.run(cmd_verbose, capture_output=True, text=True)
        
        # Try multiple regex patterns for different duration formats
        patterns = [
            r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})',  # HH:MM:SS.ss
            r'Duration: (\d{2}):(\d{2}):(\d{2}),(\d{3})',    # HH:MM:SS,sss
            r'Duration: (\d+):(\d{2}):(\d{2})',              # H+:MM:SS
            r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})',        # time=HH:MM:SS.ss from progress
        ]
        
        for pattern in patterns:
            match = re.search(pattern, result_verbose.stderr)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    hours, minutes, seconds, subseconds = groups
                    if len(subseconds) == 3:  # milliseconds
                        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(subseconds) / 1000
                    else:  # centiseconds
                        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(subseconds) / 100
                else:  # No subseconds
                    hours, minutes, seconds = groups
                    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                
                if total_seconds > 0:
                    logger.info(f"Duration found via pattern {pattern}: {total_seconds} seconds for {file_path}")
                    return float(total_seconds)
        
        # Method 6: Try mediainfo if available
        try:
            cmd_mediainfo = ["mediainfo", "--Output=General;%Duration%", file_path]
            result_mediainfo = subprocess.run(cmd_mediainfo, capture_output=True, text=True)
            if result_mediainfo.returncode == 0:
                duration_ms = result_mediainfo.stdout.strip()
                if duration_ms and duration_ms.isdigit():
                    duration_seconds = float(duration_ms) / 1000.0
                    if duration_seconds > 0:
                        logger.info(f"Duration found via mediainfo: {duration_seconds} seconds for {file_path}")
                        return duration_seconds
        except FileNotFoundError:
            logger.debug(f"mediainfo not installed, skipping for {file_path}")

        # If we absolutely cannot determine duration, raise an error instead of guessing
        logger.error(f"Cannot determine duration for {file_path}. File may be corrupted or in an unsupported format.")
        raise ValueError(f"Cannot determine duration for {file_path}. File may be corrupted or in an unsupported format.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ffprobe/ffmpeg on {file_path}: {e}")
        logger.debug(f"Command output: {e.stdout if hasattr(e, 'stdout') else 'N/A'}")
        logger.debug(f"Command error: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
        raise ValueError(f"Failed to analyze audio file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting audio duration for {file_path}: {e}", exc_info=True)
        raise

def split_audio(input_path: str, output_dir: str, segment_duration: int = MAX_DURATION) -> List[str]:
    """Split audio file into segments using FFmpeg"""
    try:
        logger.debug(f"Splitting audio file {input_path} into {segment_duration}s segments")
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

        logger.info(f"Successfully split {input_path} into {len(segments)} segments")
        return segments
    except subprocess.CalledProcessError as e:
        logger.error(f"Error splitting audio file {input_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error splitting audio: {str(e)}")

async def transcribe_with_gigaam(audio_path: str) -> str:
    """Transcribe audio file using Gigaam model"""
    global model, TRANSCRIPTION_SEMAPHORE

    if model is None:
        logger.error(f"Transcription model not available for file: {audio_path}")
        raise HTTPException(status_code=503, detail="Transcription model not available. Service is starting up or model failed to load.")

    if TRANSCRIPTION_SEMAPHORE is None:
        logger.error(f"Service not properly initialized for file: {audio_path}")
        raise HTTPException(status_code=500, detail="Service not properly initialized")

    try:
        # Limit concurrent transcriptions using semaphore
        async with TRANSCRIPTION_SEMAPHORE:
            logger.debug(f"Starting transcription for file: {audio_path}")
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None,
                model.transcribe,
                audio_path
            )
            logger.debug(f"Transcription completed for file: {audio_path}, length: {len(transcription)}")
            return transcription
    except Exception as e:
        logger.error(f"Transcription failed for file {audio_path}: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file. If longer than 29 seconds, splits into chunks first.
    Returns only the full transcription text.
    """
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"[{request_id}] Starting transcription request for file: {file.filename}, content_type: {file.content_type}")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        if not file.filename or not file.filename.lower().endswith(".webm"):
            logger.warning(f"[{request_id}] Invalid file type - filename: {file.filename}, content_type: {file.content_type}")
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
            logger.info(f"[{request_id}] File saved to: {input_path}, size: {os.path.getsize(input_path)} bytes")
        except Exception as e:
            logger.error(f"[{request_id}] Error saving file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
        
        try:
            # Try to get audio duration
            logger.info(f"[{request_id}] Getting duration for: {input_path}")
            try:
                duration = get_audio_duration(input_path)
                logger.info(f"[{request_id}] Audio duration: {duration} seconds")
            except ValueError as e:
                logger.warning(f"[{request_id}] Could not determine duration: {e}")
                logger.info(f"[{request_id}] Attempting direct transcription without duration check")
                # Try to transcribe directly without knowing duration
                # If it fails due to being too long, split it with trial segments
                try:
                    transcription = await transcribe_with_gigaam(input_path)
                    logger.info(f"[{request_id}] Direct transcription successful")
                    return JSONResponse(content={
                        "filename": file.filename,
                        "duration": "unknown",
                        "transcription": transcription
                    })
                except Exception as transcribe_error:
                    logger.warning(f"[{request_id}] Direct transcription failed: {transcribe_error}")
                    logger.info(f"[{request_id}] Attempting to split file with default segment size")
                    # Try splitting with default segment size
                    segments_dir = os.path.join(temp_dir, "segments")
                    os.makedirs(segments_dir, exist_ok=True)
                    segments = split_audio(input_path, segments_dir, MAX_DURATION)
                    logger.info(f"[{request_id}] Created {len(segments)} segments")
                    
                    transcriptions = []
                    for i, segment_path in enumerate(segments):
                        logger.info(f"[{request_id}] Transcribing segment {i+1}/{len(segments)}: {segment_path}")
                        transcription = await transcribe_with_gigaam(segment_path)
                        transcriptions.append(transcription)

                    full_text = " ".join(transcriptions)
                    logger.info(f"[{request_id}] Segmented transcription completed, total segments: {len(segments)}")
                    return JSONResponse(content={
                        "filename": file.filename,
                        "duration": "unknown (segmented)",
                        "transcription": full_text
                    })
            
            transcriptions = []
            
            if duration <= MAX_DURATION:
                # File is short enough, transcribe directly
                logger.info(f"[{request_id}] File is short ({duration}s), transcribing directly")
                transcription = await transcribe_with_gigaam(input_path)
                transcriptions.append(transcription)
            else:
                # Split file into segments
                logger.info(f"[{request_id}] File is long ({duration}s), splitting into segments")
                segments_dir = os.path.join(temp_dir, "segments")
                os.makedirs(segments_dir, exist_ok=True)

                segments = split_audio(input_path, segments_dir, MAX_DURATION)
                logger.info(f"[{request_id}] Created {len(segments)} segments")

                # Transcribe each segment
                for i, segment_path in enumerate(segments):
                    logger.info(f"[{request_id}] Transcribing segment {i+1}/{len(segments)}: {segment_path}")
                    transcription = await transcribe_with_gigaam(segment_path)
                    transcriptions.append(transcription)
            
            # Combine all transcriptions
            full_text = " ".join(transcriptions)
            logger.info(f"[{request_id}] Transcription completed successfully. Length: {len(full_text)} characters")

            return JSONResponse(content={
                "filename": file.filename,
                "duration": duration,
                "transcription": full_text
            })

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Processing error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import ssl
    
    # Check if SSL certificates are available
    ssl_cert_path = os.environ.get('SSL_CERT_PATH', '/app/certs/fullchain.pem')
    ssl_key_path = os.environ.get('SSL_KEY_PATH', '/app/certs/privkey.pem')
    
    if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        # Get worker configuration from environment
        workers = int(os.environ.get('UVICORN_WORKERS', '4'))  # Default to 4 workers
        print(f"SSL certificates found, starting HTTPS server on port 4443 with {workers} workers")

        # Check if we should run in development mode (HTTP for internal communication)
        dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'

        if dev_mode:
            # Development mode: HTTP only for internal Docker communication
            print("Running in development mode (HTTP)")
            uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=4443,
                workers=workers,
                access_log=True
            )
        else:
            # Production mode: HTTPS for external access
            print("Running in production mode (HTTPS)")
            uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=4443,
                workers=workers,
                ssl_certfile=ssl_cert_path,
                ssl_keyfile=ssl_key_path,
                access_log=True
            )
    else:
        print("ERROR: SSL certificates not found. HTTPS-only mode requires certificates.")
        print(f"Expected cert: {ssl_cert_path}")
        print(f"Expected key: {ssl_key_path}")
        raise FileNotFoundError("SSL certificates are required for HTTPS-only mode") 