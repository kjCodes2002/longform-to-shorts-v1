"""
Subtitle generation from word-level timestamps.

Generates SRT (and eventually ASS) subtitle files for individual video clips
using the word-level timestamps returned by AssemblyAI.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum number of words per subtitle chunk
MAX_WORDS_PER_CHUNK = 6


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert a float timestamp (seconds) to SRT time format HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(
    words: list[dict],
    segment_start: float,
    segment_end: float,
    output_path: str | Path,
) -> Path:
    """
    Generate an SRT subtitle file for a clip spanning [segment_start, segment_end].

    Words are filtered to the segment time range, chunked into groups of
    MAX_WORDS_PER_CHUNK, and written with timestamps rebased to 0
    (since each clip starts at time 0 in the output video).

    Args:
        words: Full list of word dicts with 'text', 'start', 'end', 'confidence'.
        segment_start: Start time of the clip in the source video (seconds).
        segment_end: End time of the clip in the source video (seconds).
        output_path: Where to write the .srt file.

    Returns:
        Path to the generated SRT file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter words that fall within the segment (with a small tolerance)
    tolerance = 0.05
    segment_words = [
        w for w in words
        if w["end"] > segment_start - tolerance and w["start"] < segment_end + tolerance
    ]

    if not segment_words:
        logger.warning(
            f"No words found for segment [{segment_start:.2f}, {segment_end:.2f}]. "
            "Writing empty SRT."
        )
        output_path.write_text("", encoding="utf-8")
        return output_path

    # Chunk words into groups of MAX_WORDS_PER_CHUNK
    chunks: list[list[dict]] = []
    for i in range(0, len(segment_words), MAX_WORDS_PER_CHUNK):
        chunks.append(segment_words[i : i + MAX_WORDS_PER_CHUNK])

    # Build SRT content with timestamps rebased to 0
    srt_lines: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        # Rebase timestamps so the clip starts at 0
        chunk_start = max(0.0, chunk[0]["start"] - segment_start)
        chunk_end = max(chunk_start + 0.1, chunk[-1]["end"] - segment_start)

        text = " ".join(w["text"] for w in chunk)

        srt_lines.append(str(idx))
        srt_lines.append(
            f"{_seconds_to_srt_time(chunk_start)} --> {_seconds_to_srt_time(chunk_end)}"
        )
        srt_lines.append(text)
        srt_lines.append("")  # blank line separator

    output_path.write_text("\n".join(srt_lines), encoding="utf-8")
    logger.info(
        f"Generated SRT with {len(chunks)} chunks for segment "
        f"[{segment_start:.2f}s – {segment_end:.2f}s] → {output_path.name}"
    )
    return output_path


def generate_ass(
    words: list[dict],
    segment_start: float,
    segment_end: float,
    output_path: str | Path,
    style: dict | None = None,
) -> Path:
    """
    Generate an ASS (Advanced SubStation Alpha) subtitle file.

    This is a placeholder for Phase 3 — styled captions with custom fonts,
    colors, and positioning.

    Args:
        words: Full list of word dicts.
        segment_start: Start time of the clip (seconds).
        segment_end: End time of the clip (seconds).
        output_path: Where to write the .ass file.
        style: Optional dict with style overrides (font, color, size, etc.).

    Raises:
        NotImplementedError: ASS generation is not yet implemented.
    """
    raise NotImplementedError(
        "ASS subtitle generation is planned for Phase 3. "
        "Use generate_srt() for now."
    )
