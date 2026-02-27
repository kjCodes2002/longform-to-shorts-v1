"""
Pipeline API route — POST /api/process-video
"""

import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from scripts.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessVideoRequest(BaseModel):
    video_path: str = Field(..., description="Path to the source video file")
    n_answers: int = Field(default=1, ge=1, le=10, description="Number of highlight sets to generate")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")


class ClipResult(BaseModel):
    path: str
    segments: list[dict]


class ProcessVideoResponse(BaseModel):
    status: str
    clips: list[ClipResult]
    errors: list[str]


@router.post("/process-video", response_model=ProcessVideoResponse)
async def process_video(request: ProcessVideoRequest):
    """
    Process a video to extract highlight clips.
    """
    logger.info(f"API request: process video '{request.video_path}' with {request.n_answers} highlight set(s)")

    try:
        result = await run_pipeline(
            video_path=request.video_path,
            n_answers=request.n_answers,
            model=request.model,
            temperature=request.temperature,
        )
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if result["status"] == "error" and not result["clips"]:
        raise HTTPException(status_code=400, detail=result["errors"])

    return result
