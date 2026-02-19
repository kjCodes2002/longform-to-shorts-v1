import subprocess
import os
from pathlib import Path

def extract_audio(video_path: str, output_dir="audio") -> Path:
    """
    Extracts audio from a video file using ffmpeg and saves it as a WAV file.
    """
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_audio = Path(output_dir) / (video_path_obj.stem + ".wav")

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path_obj),
        "-vn",          # No video
        "-sn",          # No subtitles
        "-dn",          # No data
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        str(output_audio)
    ]

    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_audio

def get_extracted_audio(video_path: str, output_dir: str = "audio") -> Path:
    """
    Gets the path to the extracted audio file, extracting it if it doesn't exist.
    """
    video_path_obj = Path(video_path)
    output_audio = Path(output_dir) / (video_path_obj.stem + ".wav")
    
    if output_audio.exists():
        return output_audio
    
    return extract_audio(video_path, output_dir)
