import subprocess
from pathlib import Path
import shutil

def clip_video(
    video_path: str,
    start_times: list[str | float | int],
    end_times: list[str | float | int],
    output_file: str = "clipped/combined.mp4",
) -> Path:
    """
    Clips segments from a video and saves them as a SINGLE combined video file.

    Args:
        video_path: Path to the source video file.
        start_times: List of start timestamps (e.g., ["10", "12.5", "00:02:30"]).
        end_times: List of end timestamps (e.g., ["20", "15.0", "00:03:15"]).
        output_file: Path to the final combined output video file.

    Returns:
        Path: Path to the combined video file.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If start_times and end_times have different lengths, are empty, or ffmpeg fails.
        subprocess.CalledProcessError: If ffmpeg fails.
    """
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if len(start_times) != len(end_times):
        raise ValueError(
            f"start_times ({len(start_times)}) and end_times ({len(end_times)}) must have the same length."
        )

    if len(start_times) == 0:
        raise ValueError("start_times and end_times must not be empty.")

    output_file_path = Path(output_file)
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary directory for intermediate clips
    # We use a subdirectory in the same folder as output to avoid cross-device link issues if /tmp is different
    temp_dir = output_file_path.parent / "temp_clips"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    clipped_paths = []

    try:
        # 1. Create individual clips
        for i, (start, end) in enumerate(zip(start_times, end_times), start=1):
            # Using .mp4 for intermediate clips to avoid issues, or match input suffix
            clip_name = f"clip_{i}{video_path_obj.suffix}"
            clip_path = temp_dir / clip_name

            # Re-encoding to ensure consistent streams for concatenation
            # Using -c:v libx264 -c:a aac to standardize
            command_clip = [
                "ffmpeg",
                "-y",
                "-i", str(video_path_obj),
                "-ss", start,
                "-to", end,
                "-c:v", "libx264",
                "-c:a", "aac",
                # faststart helpful for web playback, though not strictly needed for intermediate
                str(clip_path),
            ]

            print(f"[{i}/{len(start_times)}] Clipping {start} -> {end} ...")
            subprocess.run(command_clip, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clipped_paths.append(clip_path)

        # 2. Create concatenation list file
        concat_list_path = temp_dir / "concat_list.txt"
        with open(concat_list_path, "w") as f:
            for clip_path in clipped_paths:
                # ffmpeg requires paths to be escaped
                # Just using absolute path with forward slashes usually works best
                safe_path = str(clip_path.resolve()).replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        # 3. Concatenate clips
        print(f"Concatenating {len(clipped_paths)} clips into {output_file_path}...")
        command_concat = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(output_file_path),
        ]
        
        subprocess.run(command_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"Done! Saved to: {output_file_path}")
        return output_file_path

    finally:
        # 4. Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    video_dir = project_root / "video"
    output_clip_dir = project_root / "clipped"
    
    # We'll save the combined file inside 'clipped'
    final_output_file = output_clip_dir / "combined_clips.mp4"

    video_file = video_dir / "ffmpeg.mp4"

    # Updated timestamps using seconds directly to avoid format issues with >60 seconds
    start_times = ["0.0", "14.4", "26.0", "48.9", "75.0", "91.7"]
    end_times   = ["7.8", "19.2", "33.5", "55.6", "80.7", "92.6"]

    try:
        result_path = clip_video(
            video_path=str(video_file),
            start_times=start_times,
            end_times=end_times,
            output_file=str(final_output_file),
        )
    except Exception as e:
        print(f"Error: {e}")
