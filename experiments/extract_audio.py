import subprocess
from pathlib import Path

def extract_audio(video_path: str, output_dir="audio"):
    Path(output_dir).mkdir(exist_ok=True)

    output_audio = Path(output_dir) / (Path(video_path).stem + ".wav")

    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        str(output_audio)
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_audio

if __name__ == "__main__":
    video_dir = Path("video")
    for video_file in video_dir.iterdir():
        if video_file.is_file():
            extract_audio(str(video_file), output_dir="audio")
