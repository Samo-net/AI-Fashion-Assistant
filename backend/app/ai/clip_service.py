"""
CLIP Service
============
Handles clothing image classification and semantic wardrobe search using
openai/clip-vit-base-patch32 via HuggingFace Transformers.

Responsibilities:
  - Compute image embeddings for uploaded wardrobe items
  - Classify garment type, color, pattern, and formality via label bank cosine similarity
  - Store 512-dim embeddings in pgvector for semantic search
  - Semantic search: encode text query → cosine similarity vs stored embeddings

Nigerian garment vocabulary is included in the label bank from day one.
"""

import logging
from functools import lru_cache
from typing import Optional
import io

import numpy as np
import httpx
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

# Lazy-loaded model — only imported when this module is first used
_clip_model = None
_clip_processor = None
_label_embeddings: dict[str, np.ndarray] = {}  # precomputed per category

# ── Label Bank ─────────────────────────────────────────────────────────────
# Grouped by classification axis. Extend freely.

CATEGORY_LABELS = [
    # Western
    "t-shirt", "shirt", "blouse", "jacket", "coat", "hoodie", "sweater",
    "trousers", "jeans", "shorts", "skirt", "dress", "suit", "tie",
    "shoes", "sneakers", "boots", "sandals", "heels",
    "bag", "belt", "hat", "sunglasses", "watch", "scarf",
    # Nigerian traditional
    "ankara dress", "ankara top", "ankara skirt", "ankara fabric",
    "agbada", "senator suit", "kaftan", "buba", "iro and buba",
    "aso-oke gele", "aso-oke fabric", "lace fabric", "lace dress",
    "isiagu", "adire fabric", "dashiki", "fila cap",
]

COLOR_LABELS = [
    "red", "blue", "green", "yellow", "orange", "purple", "pink",
    "black", "white", "grey", "brown", "beige", "cream", "navy",
    "maroon", "gold", "silver", "multicolor", "ankara pattern colors",
]

PATTERN_LABELS = [
    "solid color", "ankara print", "kente pattern", "lace pattern",
    "stripe", "check", "floral", "polka dot", "abstract print",
    "adire pattern", "plain fabric",
]

FORMALITY_LABELS = [
    "casual wear", "smart casual", "formal business wear",
    "traditional ceremony outfit", "party wear", "religious service wear",
    "wedding guest outfit", "sportswear",
]


def _get_model():
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor
        logger.info("Loading CLIP model openai/clip-vit-base-patch32 ...")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_model.eval()
        logger.info("CLIP model loaded.")
    return _clip_model, _clip_processor


def _encode_texts(texts: list[str]) -> np.ndarray:
    import torch
    model, processor = _get_model()
    inputs = processor(text=texts, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        features = model.get_text_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy()


def _encode_image(image: Image.Image) -> np.ndarray:
    import torch
    model, processor = _get_model()
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy()[0]  # shape (512,)


def _cosine_top1(embedding: np.ndarray, label_embeddings: np.ndarray) -> int:
    scores = label_embeddings @ embedding
    return int(np.argmax(scores))


def precompute_label_embeddings():
    """Call once at service startup to cache all label embeddings."""
    global _label_embeddings
    logger.info("Precomputing CLIP label embeddings ...")
    _label_embeddings["category"] = _encode_texts(CATEGORY_LABELS)
    _label_embeddings["color"] = _encode_texts(COLOR_LABELS)
    _label_embeddings["pattern"] = _encode_texts(PATTERN_LABELS)
    _label_embeddings["formality"] = _encode_texts(FORMALITY_LABELS)
    logger.info("Label embeddings ready.")


async def _fetch_image(url: str) -> Image.Image:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


async def classify_and_embed(image_url: str) -> dict:
    """
    Download image, compute CLIP embedding, and classify all axes.
    Returns a dict with: embedding (list[float]), category, color, pattern, formality
    """
    if not _label_embeddings:
        precompute_label_embeddings()

    image = await _fetch_image(image_url)
    embedding = _encode_image(image)  # (512,)

    category_idx = _cosine_top1(embedding, _label_embeddings["category"])
    color_idx = _cosine_top1(embedding, _label_embeddings["color"])
    pattern_idx = _cosine_top1(embedding, _label_embeddings["pattern"])
    formality_idx = _cosine_top1(embedding, _label_embeddings["formality"])

    return {
        "embedding": embedding.tolist(),  # stored as pgvector vector
        "category": CATEGORY_LABELS[category_idx],
        "primary_color": COLOR_LABELS[color_idx],
        "pattern": PATTERN_LABELS[pattern_idx],
        "formality": FORMALITY_LABELS[formality_idx],
    }


async def search_wardrobe(
    db: AsyncSession, user_id: str, query: str, limit: int = 10
) -> list:
    """
    Encode text query with CLIP, then find closest wardrobe items using
    pgvector's <=> cosine-distance operator (SQL-native, uses ivfflat index).
    """
    from app.models.wardrobe import WardrobeItem
    from sqlalchemy.orm import selectinload

    if not _label_embeddings:
        precompute_label_embeddings()

    query_embedding = _encode_texts([query])[0].tolist()  # list[float]

    result = await db.execute(
        select(WardrobeItem)
        .options(selectinload(WardrobeItem.tags))
        .where(
            and_(
                WardrobeItem.user_id == user_id,
                WardrobeItem.is_active == True,
                WardrobeItem.clip_embedding.is_not(None),
            )
        )
        .order_by(WardrobeItem.clip_embedding.op("<=>")(query_embedding))
        .limit(limit)
    )
    return result.scalars().all()
