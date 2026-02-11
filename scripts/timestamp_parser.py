import re

def parse_timestamps(text: str) -> list[tuple[str, str]]:
    """
    Extracts start and end timestamps from text output.
    Looks for patterns like [0.0s – 7.8s], (14.4s - 19.2s), [75s - 80s], etc.
    
    Args:
        text: The text string containing timestamps.
        
    Returns:
        list[tuple[str, str]]: A list of (start_time, end_time) as strings.
    """
    # Regex breakdown:
    # (?:\[|\()     : Opening bracket or parenthesis
    # ([\d.]+)       : Captured group 1 (start time)
    # s?             : Optional 's' for seconds
    # \s*[\-–—]\s*   : Separator (space, hyphen/en-dash/em-dash, space)
    # ([\d.]+)       : Captured group 2 (end time)
    # s?             : Optional 's' for seconds
    # (?:\]|\))     : Closing bracket or parenthesis
    
    pattern = r"(?:\[|\()([\d.]+)s?\s*[\-–—]\s*([\d.]+)s?(?:\]|\))"
    
    matches = re.findall(pattern, text)
    return matches
