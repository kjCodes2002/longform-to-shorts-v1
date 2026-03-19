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


# ---------------------------------------------------------------------------
# ASS constants & helpers
# ---------------------------------------------------------------------------

# Default style settings for viral-style captions
_DEFAULT_ASS_STYLE = {
    "font": "Montserrat",              # Modern bold font (fallback: Arial Black)
    "fontsize": 72,                    # Bigger = more reel-like
    "primary_color": "&H00FFFFFF",     # White
    "highlight_color": "&H0000A5FF",   # Orange-ish
    "outline_color": "&H00000000",     # Black outline
    "shadow_color": "&H80000000",      # Soft shadow

    "border_style": 1,
    "outline": 0,                      # No outline 
    "shadow": 2,                       # Slight depth

    "alignment": 8,                    # top-center (\an8)
    "margin_v": 80
}

# Number of surrounding "context" words shown alongside the highlighted word
_CONTEXT_WORDS = 2


def _seconds_to_ass_time(seconds: float) -> str:
    """Convert a float timestamp (seconds) to ASS time format H:MM:SS.cc."""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _build_ass_header(s: dict) -> str:
    """Build the [Script Info], [V4+ Styles], and [Events] header."""
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 720\n"
        "PlayResY: 1280\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{s['font']},{s['fontsize']},"
        f"{s['primary_color']},{s['primary_color']},"
        f"{s['outline_color']},{s['shadow_color']},"
        f"-1,0,0,0,100,100,0,0,"
        f"{s['border_style']},{s['outline']},{s['shadow']},"
        f"{s['alignment']},10,10,{s['margin_v']},1\n"
        f"Style: Highlight,{s['font']},{s['fontsize']},"
        f"{s['highlight_color']},{s['highlight_color']},"
        f"{s['outline_color']},{s['shadow_color']},"
        f"-1,0,0,0,100,100,0,0,"
        f"{s['border_style']},{s['outline']},{s['shadow']},"
        f"{s['alignment']},10,10,{s['margin_v']},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def generate_ass(
    words: list[dict],
    segment_start: float,
    segment_end: float,
    output_path: str | Path,
    style: dict | None = None,
) -> Path:
    """
    Generate an ASS subtitle file with viral-style word-by-word animated captions.

    Each word becomes its own Dialogue event.  The current word is rendered in
    a yellow "Highlight" style with a slight scale-pop and fade effect, while
    a few surrounding context words are shown simultaneously in white so the
    viewer can follow along.

    Args:
        words: Full list of word dicts with 'text', 'start', 'end', 'confidence'.
        segment_start: Start time of the clip in the source video (seconds).
        segment_end: End time of the clip in the source video (seconds).
        output_path: Where to write the .ass file.
        style: Optional dict with style overrides (keys from _DEFAULT_ASS_STYLE).

    Returns:
        Path to the generated ASS file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Merge user style overrides
    s = {**_DEFAULT_ASS_STYLE, **(style or {})}

    # Filter words to the segment time range
    tolerance = 0.05
    segment_words = [
        w for w in words
        if w["end"] > segment_start - tolerance and w["start"] < segment_end + tolerance
    ]

    # Build the ASS file
    header = _build_ass_header(s)

    if not segment_words:
        logger.warning(
            f"No words found for segment [{segment_start:.2f}, {segment_end:.2f}]. "
            "Writing ASS with header only."
        )
        output_path.write_text(header, encoding="utf-8")
        return output_path

    dialogue_lines: list[str] = []

    for i, word in enumerate(segment_words):
        # Rebase to clip time (clip starts at 0)
        w_start = max(0.0, word["start"] - segment_start)
        w_end_raw = max(w_start + 0.05, word["end"] - segment_start)

        # To prevent flickering between words, extend the end time of the current word
        # to match exactly the start time of the next word, provided the gap isn't huge.
        w_end = w_end_raw
        if i + 1 < len(segment_words):
            next_start = max(0.0, segment_words[i+1]["start"] - segment_start)
            gap = next_start - w_end_raw
            if 0 < gap < 0.5:  # If silence is less than 500ms, bridge the gap
                w_end = next_start
            elif gap <= 0:
                # If they already overlap or touch, just use the raw end (or let ASS handle overlap)
                w_end = max(w_end_raw, next_start)

        # --- Build the text with context words ---
        # Show a window of words: context before + HIGHLIGHTED current + context after
        ctx_start = max(0, i - _CONTEXT_WORDS)
        ctx_end = min(len(segment_words), i + _CONTEXT_WORDS + 1)

        parts: list[str] = []
        for j in range(ctx_start, ctx_end):
            w_text = segment_words[j]["text"]
            if j == i:
                # Current word: highlighted (just color change, no scale/fade to avoid blinking)
                parts.append(
                    r"{\rHighlight}"
                    + w_text
                    + r"{\r}"
                )
            else:
                # Context word: default white style
                parts.append(w_text)

        line_text = " ".join(parts)

        dialogue_lines.append(
            f"Dialogue: 0,{_seconds_to_ass_time(w_start)},{_seconds_to_ass_time(w_end)},"
            f"Default,,0,0,0,,{line_text}"
        )

    content = header + "\n".join(dialogue_lines) + "\n"
    output_path.write_text(content, encoding="utf-8")

    logger.info(
        f"Generated ASS with {len(dialogue_lines)} word events for segment "
        f"[{segment_start:.2f}s – {segment_end:.2f}s] → {output_path.name}"
    )
    return output_path
