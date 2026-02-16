"""
Word-level matching using AssemblyAI word timestamps.

This module matches LLM-extracted phrases to word sequences in the transcript,
providing precise timestamps for video clipping.
"""

from difflib import SequenceMatcher


def match_phrase_to_words(
    phrase: str,
    words: list[dict],
    threshold: float = 0.8
) -> tuple[float, float, str] | None:
    """
    Matches a phrase to a sequence of words and returns precise timestamps.
    
    Args:
        phrase: The phrase to match (from LLM output)
        words: List of word dicts with 'text', 'start', 'end', 'confidence'
        threshold: Minimum similarity ratio (0-1) to consider a match
    
    Returns:
        tuple[float, float, str] | None: (start_time, end_time, matched_text)
        Returns None if no match found above threshold
    """
    phrase_clean = phrase.strip().lower()
    phrase_words = phrase_clean.split()
    
    if not phrase_words or not words:
        return None
    
    # Try to find contiguous match first (exact or near-exact)
    best_match = None
    best_score = 0.0
    
    # Search for contiguous word sequence match
    for i in range(len(words) - len(phrase_words) + 1):
        # Try matching phrase_words to words[i:i+len(phrase_words)]
        window_words = words[i:i + len(phrase_words)]
        window_text = " ".join(w["text"].lower() for w in window_words)
        
        # Check if phrase words match window words
        if _words_match(phrase_words, [w["text"].lower() for w in window_words]):
            start_time = window_words[0]["start"]
            end_time = window_words[-1]["end"]
            matched_text = " ".join(w["text"] for w in window_words)
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, phrase_clean, window_text).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = (start_time, end_time, matched_text)
    
    # If we found a good match, return it
    if best_match and best_score >= threshold:
        return best_match
    
    # Fallback: fuzzy matching with word overlap
    best_match = None
    best_score = 0.0
    
    # Try sliding window approach with fuzzy matching
    for window_size in range(len(phrase_words), min(len(phrase_words) + 5, len(words) + 1)):
        for i in range(len(words) - window_size + 1):
            window_words = words[i:i + window_size]
            window_text = " ".join(w["text"].lower() for w in window_words)
            
            # Calculate word overlap ratio
            overlap_ratio = _word_overlap_ratio(phrase_words, [w["text"].lower() for w in window_words])
            similarity = SequenceMatcher(None, phrase_clean, window_text).ratio()
            
            # Combined score (weighted towards overlap)
            combined_score = (overlap_ratio * 0.7) + (similarity * 0.3)
            
            if combined_score > best_score:
                best_score = combined_score
                start_time = window_words[0]["start"]
                end_time = window_words[-1]["end"]
                matched_text = " ".join(w["text"] for w in window_words)
                best_match = (start_time, end_time, matched_text)
    
    if best_match and best_score >= threshold:
        return best_match
    
    return None


def match_phrases_to_words(
    phrases: list[str],
    words: list[dict],
    threshold: float = 0.8
) -> list[tuple[float, float, str]]:
    """
    Matches multiple phrases to word sequences.
    
    Args:
        phrases: List of phrases to match
        words: List of word dicts with timestamps
        threshold: Minimum similarity threshold
    
    Returns:
        list[tuple[float, float, str]]: List of (start, end, matched_text) tuples
    """
    results = []
    
    for phrase in phrases:
        match = match_phrase_to_words(phrase, words, threshold)
        if match:
            results.append(match)
        else:
            print(f"  [word_matcher] No match found for: \"{phrase[:60]}...\"")
    
    return results


def _words_match(phrase_words: list[str], window_words: list[str]) -> bool:
    """
    Check if phrase words match window words (allowing for minor differences).
    
    Args:
        phrase_words: Words from the phrase
        window_words: Words from the window
    
    Returns:
        bool: True if words match (with fuzzy tolerance)
    """
    if len(phrase_words) != len(window_words):
        return False
    
    # Check if all words match (with fuzzy matching for minor differences)
    matches = 0
    for p_word, w_word in zip(phrase_words, window_words):
        # Exact match
        if p_word == w_word:
            matches += 1
        # Fuzzy match (for punctuation differences, etc.)
        elif SequenceMatcher(None, p_word, w_word).ratio() >= 0.85:
            matches += 1
    
    # Require at least 80% of words to match
    return matches >= len(phrase_words) * 0.8


def _word_overlap_ratio(phrase_words: list[str], window_words: list[str]) -> float:
    """
    Calculate the ratio of phrase words found in window words.
    
    Args:
        phrase_words: Words from the phrase
        window_words: Words from the window
    
    Returns:
        float: Ratio between 0 and 1
    """
    if not phrase_words:
        return 0.0
    
    phrase_set = set(phrase_words)
    window_set = set(window_words)
    
    # Count matches (including fuzzy matches)
    matches = 0
    for p_word in phrase_set:
        # Check for exact match
        if p_word in window_set:
            matches += 1
        else:
            # Check for fuzzy match
            for w_word in window_set:
                if SequenceMatcher(None, p_word, w_word).ratio() >= 0.85:
                    matches += 1
                    break
    
    return matches / len(phrase_set)
