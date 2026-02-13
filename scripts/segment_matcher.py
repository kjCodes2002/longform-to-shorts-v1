import re
from difflib import SequenceMatcher


def extract_lines_from_answer(answer_text: str) -> list[str]:
    """
    Extracts verbatim text lines from the LLM's bulleted answer.
    Strips bullet markers, quotes, and timestamps.

    Args:
        answer_text: The raw LLM output.

    Returns:
        list[str]: Cleaned text lines.
    """
    lines = []
    for line in answer_text.strip().split("\n"):
        line = line.strip()
        # Skip empty lines and non-bullet lines
        if not line or not line.startswith("-"):
            continue
        # Remove bullet marker
        line = line.lstrip("-").strip()
        # Remove surrounding quotes if present
        line = line.strip('"').strip("'").strip(""").strip(""").strip()
        # Remove any trailing timestamp patterns like [0.0s – 7.8s]
        line = re.sub(r'\s*[\[\(][\d.]+s?\s*[\-–—]\s*[\d.]+s?[\]\)]\s*$', '', line)
        if line:
            lines.append(line)
    return lines


def match_lines_to_segments(
    lines: list[str],
    whisper_segments: list[dict],
    threshold: float = 0.5,
) -> list[tuple[float, float, str]]:
    """
    Matches each LLM-output line to the original Whisper segments using
    substring and fuzzy matching. Returns the original Whisper timestamps.

    Args:
        lines: Verbatim text lines extracted from the LLM answer.
        whisper_segments: The raw Whisper segments list (each has 'start', 'end', 'text').
        threshold: Minimum similarity ratio to consider a match.

    Returns:
        list[tuple[float, float, str]]: List of (start, end, matched_text) using
        the original Whisper timestamps.
    """
    results = []

    for line in lines:
        best_match = _find_best_match(line, whisper_segments, threshold)
        if best_match:
            results.append(best_match)
        else:
            print(f"  [segment_matcher] No match found for: \"{line[:60]}...\"")

    return results


def _find_best_match(
    line: str,
    segments: list[dict],
    threshold: float,
) -> tuple[float, float, str] | None:
    """
    Finds the best matching segment(s) for a given line.
    Handles three cases:
      1. Line is a substring of one segment (exact containment).
      2. Line spans multiple consecutive segments.
      3. Fuzzy match fallback.
    """
    line_clean = line.strip().lower()

    # --- Case 1: Exact substring match within a single segment ---
    for seg in segments:
        seg_text = seg['text'].strip().lower()
        if line_clean in seg_text or seg_text in line_clean:
            return (seg['start'], seg['end'], seg['text'].strip())

    # --- Case 2: Line spans multiple consecutive segments ---
    # Build a sliding window of consecutive segments
    for window_size in range(2, min(5, len(segments) + 1)):
        for i in range(len(segments) - window_size + 1):
            window_segs = segments[i:i + window_size]
            combined_text = " ".join(s['text'].strip() for s in window_segs).lower()
            if line_clean in combined_text or combined_text in line_clean:
                return (
                    window_segs[0]['start'],
                    window_segs[-1]['end'],
                    " ".join(s['text'].strip() for s in window_segs),
                )

    # --- Case 3: Fuzzy match fallback ---
    best_ratio = 0
    best_seg = None
    for seg in segments:
        seg_text = seg['text'].strip().lower()
        ratio = SequenceMatcher(None, line_clean, seg_text).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_seg = seg

    if best_seg and best_ratio >= threshold:
        return (best_seg['start'], best_seg['end'], best_seg['text'].strip())

    return None
