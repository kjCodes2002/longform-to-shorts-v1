import subprocess
import shutil
import logging
from pathlib import Path

from scripts.subtitle_generator import generate_ass

logger = logging.getLogger(__name__)


def clip_video_segments(
    video_path: str,
    segments: list[tuple[str | float, str | float]],
    output_file: str,
    padding: float = 0.0,
    words: list[dict] | None = None,
) -> Path:
    """
    Clips multiple segments from a video and concatenates them into a single file.
    When *words* are provided, viral-style ASS captions are burned into each clip.

    Args:
        video_path: Path to the source video file.
        segments: List of (start_time, end_time) tuples.
        output_file: Path where the concatenated video will be saved.
        padding: Time in seconds to add before and after each segment (default 0.0).
        words: Optional list of word dicts (text/start/end/confidence) from
               the transcriber.  When provided, ASS captions are generated
               and burned into each clip via FFmpeg's ass= video filter.

    Returns:
        Path: The path to the created output file.
    """
    video_path_obj = Path(video_path).resolve()
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not segments:
        raise ValueError("No segments provided for clipping.")

    output_file_path = Path(output_file)
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a temp directory in the same parent as output to avoid cross-device moves
    temp_dir = output_file_path.parent / f"temp_{output_file_path.stem}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    clipped_paths = []

    try:
        # 1. Generate individual clips
        for i, (start, end) in enumerate(segments, 1):
            # Skip zero-duration segments to avoid ffmpeg errors
            try:
                s_val = float(start)
                e_val = float(end)

                # Apply padding (default is 0.0 now for high precision)
                s_padded = max(0, s_val - padding)
                e_padded = e_val + padding

                if abs(s_padded - e_padded) < 0.001:
                    print(f"Skipping effectively zero-duration segment: {start} -> {end}")
                    continue
            except ValueError:
                # Fallback for HH:MM:SS format
                s_padded = start
                e_padded = end

            clip_filename = f"clip_{i}{video_path_obj.suffix}"
            clip_path = temp_dir / clip_filename

            # --- Build FFmpeg command ---
            command = [
                "ffmpeg", "-y",
                "-ss", str(s_padded),
                "-t", str(max(0.1, e_val - s_val)),
                "-i", str(video_path_obj),
            ]

            # If words supplied, generate ASS and burn into the video
            if words:
                ass_filename = f"clip_{i}.ass"
                ass_path = temp_dir / ass_filename
                generate_ass(words, s_padded, e_padded, ass_path)

                # Burn captions using the ass= video filter
                command += [
                    "-vf", f"ass={ass_filename}",
                ]
                logger.info(f"  Burning ASS captions into clip {i} from {ass_filename}")

            command += [
                "-map", "0:v",
                "-map", "0:a",
                "-map_metadata", "-1",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                str(clip_path),
            ]

            # Run with cwd=temp_dir so the ass= filter resolves the
            # ASS filename without needing absolute-path escaping.
            subprocess.run(
                command, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=str(temp_dir),
            )
            clipped_paths.append(clip_path)

        if not clipped_paths:
            raise ValueError("No valid clips (duration > 0) were generated from the provided segments.")

        # 2. Create concat list
        concat_list_path = temp_dir / "concat_list.txt"
        with open(concat_list_path, "w") as f:
            for clip_path in clipped_paths:
                # Use absolute path and escape single quotes for ffmpeg
                safe_path = str(clip_path.resolve()).replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        # 3. Concatenate
        command_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-map", "0",     # Map all streams (video, audio)
            "-c", "copy",
            str(output_file_path),
        ]

        subprocess.run(command_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return output_file_path

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

