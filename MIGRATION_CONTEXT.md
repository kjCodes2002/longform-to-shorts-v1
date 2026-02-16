# Migration from Whisper to AssemblyAI

## Why the Shift?

The project migrated from OpenAI's Whisper API to **AssemblyAI** to improve the precision of video clipping for generating short reels.

### Key Drivers:
1.  **Timestamp Precision**:
    *   **Whisper API**: Provides segment-level timestamps (typically 5-15 seconds), which are too coarse for precise video cutting.
    *   **AssemblyAI**: Provides **word-level timestamps** directly in the transcription response, allowing for frame-perfect cuts.
2.  **Architecture Simplicity**:
    *   Using Whisper for accurate timestamps would likely require a second step (Forced Alignment), effectively doubling the API calls and complexity.
    *   AssemblyAI handles transcription and word-level timing in a **single API call**.
3.  **Cost Efficiency**:
    *   AssemblyAI (~$0.0025/min) is approximately **60% cheaper** than Whisper (~$0.006/min).
4.  **Accuracy**:
    *   AssemblyAI showed slightly better word accuracy (93.3%) compared to Whisper (91.6%) in our evaluations.

## How We Migrated

The migration involved replacing the transcription engine while keeping the rest of the pipeline intact.

### 1. New Dependencies
*   Added `assemblyai` python package.

### 2. Code Changes
*   **`scripts/transcriber.py`**:
    *   Replaced OpenAI Whisper client with `assemblyai.Transcriber`.
    *   Updated to return a structure containing both full text and a list of words with precise start/end times.
*   **`scripts/word_matcher.py` (New)**:
    *   Created to perform precise matching of LLM-selected phrases against the word-level timestamps.
*   **`scripts/segment_matcher.py`**:
    *   Updated to prefer word-level matching when available, falling back to segment-level matching if necessary.
*   **`scripts/main.py`**:
    *   Updated the workflow to pass word-level data through the pipeline for final clipping.

### 3. Workflow Comparison

**Old Workflow (Whisper):**
`Video` → `Audio` → `Whisper API` → `Segments (approx time)` → `LLM` → `Match to Segments` → `Approximate Clip`

**Current Workflow (AssemblyAI):**
`Video` → `Audio` → `AssemblyAI API` → `Words (precise time)` → `LLM` → `Match to Words` → **`Precise Clip`**
