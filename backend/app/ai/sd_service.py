"""
Stable Diffusion + ControlNet Visualization Service
=====================================================
Generates 2D flat-lay outfit composite images using Stable Diffusion 1.5
with ControlNet (canny edge) conditioning.

Strategy:
  - During development: use Replicate.com API (no GPU infra needed)
  - For final evaluation: switch to self-hosted pipeline on Cloud GPU

Flat-lay approach is used (not full-body mannequin) to:
  1. Avoid anatomy generation problems common with SD
  2. Produce controllable, clean fashion editorial images
  3. Reduce bias risk (no skin generation involved)

The skin tone descriptor from the user profile is embedded in the prompt
to ensure culturally appropriate representation.
"""

import asyncio
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from PIL import Image

from app.core.config import settings
from app.core.s3 import get_s3_client

logger = logging.getLogger(__name__)

# Replicate model ID for SD 1.5 + ControlNet canny
REPLICATE_MODEL = "jagilley/controlnet-canny:aff48af9c68d162388d230a2ab003f68d2638d88b154d57be2d31e1cdf2a3ba"

POSITIVE_PROMPT_TEMPLATE = (
    "fashion editorial, flat lay clothing arrangement on white background, "
    "{outfit_description}, Nigerian style aesthetic, {skin_tone_context}, "
    "professional studio lighting, high quality, 8k, clean background, "
    "product photography style"
)

NEGATIVE_PROMPT = (
    "low quality, blurry, bad anatomy, ugly, deformed, watermark, text, "
    "cluttered background, overexposed, washed out colors, unrealistic"
)


def _build_positive_prompt(outfit_description: str, skin_tone: Optional[str]) -> str:
    skin_tone_context = ""
    if skin_tone:
        skin_tone_context = f"suitable for {skin_tone} complexion"
    return POSITIVE_PROMPT_TEMPLATE.format(
        outfit_description=outfit_description,
        skin_tone_context=skin_tone_context,
    )


async def _run_via_replicate(positive_prompt: str, image_urls: list[str]) -> str:
    """
    Call Replicate API to generate outfit visualization.
    Returns the URL of the generated image.
    """
    if not settings.REPLICATE_API_TOKEN:
        raise RuntimeError("REPLICATE_API_TOKEN not configured.")

    # Use first clothing image as ControlNet conditioning input (flat-lay)
    conditioning_image_url = image_urls[0] if image_urls else None

    payload = {
        "version": REPLICATE_MODEL.split(":")[1],
        "input": {
            "prompt": positive_prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "image": conditioning_image_url,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "seed": -1,
        },
    }

    headers = {
        "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        # Create prediction
        resp = await client.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        prediction = resp.json()
        prediction_id = prediction["id"]

        # Poll until complete
        for _ in range(60):  # up to 60 × 2s = 2 min
            await asyncio.sleep(2)
            poll = await client.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers,
            )
            poll.raise_for_status()
            result = poll.json()

            if result["status"] == "succeeded":
                return result["output"][0]  # image URL
            elif result["status"] == "failed":
                raise RuntimeError(f"Replicate prediction failed: {result.get('error')}")

    raise TimeoutError("Replicate visualization timed out after 2 minutes.")


async def _upload_image_to_s3(image_url: str, user_id: str) -> tuple[str, str]:
    """Download generated image and upload to S3. Returns (s3_key, public_url)."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        image_data = resp.content

    s3_key = f"visualizations/{user_id}/{uuid.uuid4()}.png"
    s3 = get_s3_client()
    s3.put_object(
        Bucket=settings.AWS_BUCKET_NAME,
        Key=s3_key,
        Body=image_data,
        ContentType="image/png",
    )

    public_url = (
        f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    )
    return s3_key, public_url


async def generate_visualization(
    job_id: str,
    user_id: str,
    outfit_description: str,
    item_image_urls: list[str],
    skin_tone: Optional[str] = None,
) -> dict:
    """
    Main entry point for visualization generation.
    Returns dict with image_url, image_s3_key, positive_prompt.
    """
    positive_prompt = _build_positive_prompt(outfit_description, skin_tone)
    logger.info(f"Starting visualization job {job_id} for user {user_id}")

    # Route to Replicate (dev) or local SD (production)
    if settings.REPLICATE_API_TOKEN:
        generated_url = await _run_via_replicate(positive_prompt, item_image_urls)
    else:
        raise NotImplementedError(
            "Self-hosted SD pipeline not yet configured. Set REPLICATE_API_TOKEN for development."
        )

    s3_key, public_url = await _upload_image_to_s3(generated_url, user_id)

    logger.info(f"Visualization job {job_id} complete: {public_url}")
    return {
        "image_url": public_url,
        "image_s3_key": s3_key,
        "positive_prompt": positive_prompt,
        "negative_prompt": NEGATIVE_PROMPT,
    }
