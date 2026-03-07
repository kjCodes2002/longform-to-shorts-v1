"""
Clips download route — GET /api/clips/{filename}
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where clips are stored
CLIPS_DIR = Path("/tmp/longform_shorts/clipped")


@router.get("/clips/{filename}")
async def download_clip(filename: str):
    """
    Download a generated clip by filename.
    """
    # Prevent path traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    clip_path = CLIPS_DIR / filename

    if not clip_path.exists():
        raise HTTPException(status_code=404, detail=f"Clip not found: {filename}")

    logger.info(f"Serving clip: {filename}")
    return FileResponse(
        path=str(clip_path),
        media_type="video/mp4",
        filename=filename,
    )
