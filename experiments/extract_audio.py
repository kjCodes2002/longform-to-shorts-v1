import subprocess
from pathlib import Path

def extract_audio(video_path: str, output_dir="audio") -> Path:
    """
    Extracts audio from a video file using ffmpeg and saves it as a WAV file.
    
    Args:
        video_path: Path to the source video file.
        output_dir: Directory where the extracted audio will be saved.
        
    Returns:
        Path: The path to the extracted audio file.
        
    Raises:
        FileNotFoundError: If the video file does not exist.
        subprocess.CalledProcessError: If ffmpeg fails.
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
        "-vn",
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
    
    Args:
        video_path: Path to the source video file.
        output_dir: Directory where the audio should be located.
        
    Returns:
        Path: The path to the audio file.
    """
    video_path_obj = Path(video_path)
    output_audio = Path(output_dir) / (video_path_obj.stem + ".wav")
    
    if output_audio.exists():
        return output_audio
    
    return extract_audio(video_path, output_dir)

if __name__ == "__main__":
    # Define paths relative to the project root
    project_root = Path(__file__).parent.parent
    video_dir = project_root / "video"
    output_audio_dir = project_root / "audio"

    # Specifically targeting ffmpeg.mp4 as requested
    video_file = video_dir / "ffmpeg.mp4"

    try:
        print(f"Checking for audio: {video_file.stem}.wav")
        audio_path = get_extracted_audio(str(video_file), output_dir=str(output_audio_dir))
        print(f"Audio ready at: {audio_path}")
    except Exception as e:
        print(f"Error during audio extraction: {e}")
