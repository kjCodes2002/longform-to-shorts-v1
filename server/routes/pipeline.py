"""
Pipeline API route — POST /api/process-video

Accepts video via file upload (multipart/form-data).
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from scripts.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# Base directory for all temp processing files
WORK_BASE = Path("/tmp/longform_shorts")


class ClipResult(BaseModel):
    download_url: str
    filename: str
    segments: list[dict]


class ProcessVideoResponse(BaseModel):
    status: str
    clips: list[ClipResult]
    errors: list[str]


@router.post("/process-video", response_model=ProcessVideoResponse)
async def process_video(
    video: UploadFile = File(..., description="Video file to process"),
    n_answers: int = Form(default=1, ge=1, le=10, description="Number of highlight sets"),
    model: str = Form(default="gpt-4o-mini", description="OpenAI model to use"),
    temperature: float = Form(default=0.7, ge=0.0, le=2.0, description="LLM temperature"),
):
    """
    Upload a video file and extract highlight clips.

    Returns download URLs for each generated clip.
    """
    # Create a unique work directory for this job
    job_id = uuid.uuid4().hex[:12]
    work_dir = WORK_BASE / job_id
    uploads_dir = work_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    video_filename = video.filename or f"upload_{job_id}.mp4"
    video_path = uploads_dir / video_filename

    logger.info(f"[{job_id}] Receiving upload: {video_filename}")

    try:
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        await video.close()

    logger.info(f"[{job_id}] Upload saved ({video_path.stat().st_size / 1024 / 1024:.1f} MB). Starting pipeline...")

    # Run the pipeline
    try:
        result = await run_pipeline(
            video_path=str(video_path),
            n_answers=n_answers,
            model=model,
            temperature=temperature,
            work_dir=str(work_dir),
        )
    except Exception as e:
        logger.error(f"[{job_id}] Pipeline failed: {e}")
        # Clean up work directory on failure
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

    # Clean up uploaded video (keep clips)
    try:
        os.remove(video_path)
    except OSError:
        pass

    if result["status"] == "error" and not result["clips"]:
        raise HTTPException(status_code=400, detail=result["errors"])

    # Move clips to the shared clips directory and build download URLs
    shared_clips_dir = WORK_BASE / "clipped"
    shared_clips_dir.mkdir(parents=True, exist_ok=True)

    clips_response = []
    for clip in result.get("clips", []):
        clip_path = Path(clip["path"])
        if clip_path.exists():
            # Give clip a unique name to avoid collisions
            unique_name = f"{job_id}_{clip_path.name}"
            dest = shared_clips_dir / unique_name
            shutil.move(str(clip_path), str(dest))

            clips_response.append({
                "download_url": f"/api/clips/{unique_name}",
                "filename": unique_name,
                "segments": clip["segments"],
            })

    # Clean up the job work directory (audio, cache, etc.)
    shutil.rmtree(work_dir, ignore_errors=True)

    logger.info(f"[{job_id}] Done. {len(clips_response)} clip(s) ready for download.")

    return {
        "status": result["status"],
        "clips": clips_response,
        "errors": result.get("errors", []),
    }
