import subprocess
import re

def get_audio_duration(file_path):
    cmd_ffmpeg = [
        "ffmpeg", "-i", file_path, "-f", "null", "-"
    ]
    result_ffmpeg = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)
    stderr = result_ffmpeg.stderr
    
    # For WebM files without duration metadata, look for the final time in progress output
    time_matches = re.findall(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', stderr)
    if time_matches:
        # Get the last time value (final duration)
        last_time = time_matches[-1]
        hours, minutes, seconds = last_time
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        if total_seconds > 0:
            print(f"Duration found from ffmpeg progress: {total_seconds} seconds")
            return float(total_seconds)
    
    return None

# Test in container
print("Testing duration detection...")
