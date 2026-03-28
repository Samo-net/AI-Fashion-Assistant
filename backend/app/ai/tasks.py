"""
Background tasks triggered after wardrobe item upload.
These run via FastAPI BackgroundTasks (lightweight) or Celery (heavy).
"""

import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.wardrobe import WardrobeItem

logger = logging.getLogger(__name__)


async def run_clip_tagging(item_id: int) -> None:
    """
    Fetch item image → classify with CLIP → update DB with embedding + auto-tags.
    Runs as a FastAPI BackgroundTask after item creation.
    """
    from app.ai.clip_service import classify_and_embed

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(WardrobeItem).where(WardrobeItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item or not item.image_url:
                logger.warning(f"CLIP tagging skipped — item {item_id} not found or no image.")
                return

            classification = await classify_and_embed(item.image_url)

            # Only set auto-detected values if user hasn't provided them manually
            if not item.primary_color:
                item.primary_color = classification["primary_color"]
            if not item.pattern:
                item.pattern = classification["pattern"]
            if not item.formality:
                item.formality = classification["formality"]

            item.clip_embedding = classification["embedding"]
            item.clip_processed = True

            # Add auto-detected category as a tag (don't overwrite user's chosen category)
            from app.wardrobe.service import _get_or_create_tag
            from sqlalchemy.orm import selectinload

            item_with_tags = await db.execute(
                select(WardrobeItem)
                .options(selectinload(WardrobeItem.tags))
                .where(WardrobeItem.id == item_id)
            )
            item_loaded = item_with_tags.scalar_one()
            clip_tag = await _get_or_create_tag(db, f"clip:{classification['category']}")
            if clip_tag not in item_loaded.tags:
                item_loaded.tags.append(clip_tag)

            await db.commit()
            logger.info(f"CLIP tagging complete for item {item_id}: {classification['category']}")

        except Exception as e:
            await db.rollback()
            logger.error(f"CLIP tagging failed for item {item_id}: {e}")
