import asyncio
import argparse
import logging
from dotenv import load_dotenv

from scripts.pipeline import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Longform-to-Shorts Video Pipeline")
    parser.add_argument("--video", type=str, help="Path to source video", default="video/ffmpeg.mp4")
    parser.add_argument("--n_answers", type=int, help="Number of highlight sets to generate", default=1)
    parser.add_argument("--model", type=str, help="OpenAI model to use", default="gpt-4o-mini")
    parser.add_argument("--temperature", type=float, help="LLM temperature", default=0.7)
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("--- Starting Orchestrator ---")

    result = await run_pipeline(
        video_path=args.video,
        n_answers=args.n_answers,
        model=args.model,
        temperature=args.temperature,
    )

    if result["status"] == "ok":
        for clip in result["clips"]:
            logger.info(f"✅ Saved: {clip['path']}")
    else:
        for error in result["errors"]:
            logger.error(error)


if __name__ == "__main__":
    asyncio.run(main())
