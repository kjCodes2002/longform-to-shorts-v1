"""
FastAPI application for the Longform-to-Shorts pipeline.
Run with: uvicorn server.app:app --reload
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from server.routes.pipeline import router as pipeline_router
from server.routes.clips import router as clips_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="Longform-to-Shorts API",
    description="API for extracting highlight clips from long-form videos",
    version="1.0.0",
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(pipeline_router, prefix="/api")
app.include_router(clips_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Serve React frontend (built with Vite)
CLIENT_DIST = Path(__file__).parent.parent / "client" / "dist"

if CLIENT_DIST.exists():
    # Serve static assets (JS, CSS, etc.)
    app.mount("/assets", StaticFiles(directory=str(CLIENT_DIST / "assets")), name="assets")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = CLIENT_DIST / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(CLIENT_DIST / "index.html"))
