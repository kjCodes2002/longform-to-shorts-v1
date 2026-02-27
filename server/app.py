"""
FastAPI application for the Longform-to-Shorts pipeline.
Run with: uvicorn server.app:app --reload
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from server.routes.pipeline import router as pipeline_router

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

# Mount routes
app.include_router(pipeline_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
