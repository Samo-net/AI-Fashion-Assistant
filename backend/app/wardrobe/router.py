from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.core.s3 import generate_presigned_upload_url
from app.wardrobe import service
from app.wardrobe.schemas import (
    WardrobeItemCreate,
    WardrobeItemUpdate,
    WardrobeItemResponse,
    PresignedUploadResponse,
    UsageLogCreate,
    UsageLogResponse,
    SemanticSearchRequest,
)
from typing import Optional

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


# ── Upload URL ──────────────────────────────────────────────────────────────

@router.get("/upload-url", response_model=PresignedUploadResponse)
async def get_upload_url(
    extension: str = Query(default="jpg", pattern="^(jpg|jpeg|png|webp)$"),
    token: dict = Depends(verify_firebase_token),
):
    """Returns a presigned S3 POST URL for direct client-to-S3 image upload."""
    return generate_presigned_upload_url(
        file_extension=extension, folder=f"wardrobe/{token['uid']}"
    )


# ── Wardrobe Items ──────────────────────────────────────────────────────────

@router.get("/items", response_model=list[WardrobeItemResponse])
async def list_wardrobe_items(
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_items(db, token["uid"], category, limit, offset)


@router.post("/items", response_model=WardrobeItemResponse, status_code=status.HTTP_201_CREATED)
async def add_wardrobe_item(
    data: WardrobeItemCreate,
    background_tasks: BackgroundTasks,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_item(db, token["uid"], data)

    # Trigger CLIP classification in background if image is provided
    if item.image_url:
        from app.ai.tasks import run_clip_tagging
        background_tasks.add_task(run_clip_tagging, item.id)

    return item


@router.get("/items/{item_id}", response_model=WardrobeItemResponse)
async def get_wardrobe_item(
    item_id: int,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    item = await service.get_item(db, item_id, token["uid"])
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item


@router.put("/items/{item_id}", response_model=WardrobeItemResponse)
async def update_wardrobe_item(
    item_id: int,
    updates: WardrobeItemUpdate,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    item = await service.get_item(db, item_id, token["uid"])
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return await service.update_item(db, item, updates)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wardrobe_item(
    item_id: int,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    item = await service.get_item(db, item_id, token["uid"])
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    await service.delete_item(db, item)


# ── Usage Logging ───────────────────────────────────────────────────────────

@router.post("/items/{item_id}/wear", response_model=UsageLogResponse, status_code=status.HTTP_201_CREATED)
async def log_wear(
    item_id: int,
    data: UsageLogCreate,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    item = await service.get_item(db, item_id, token["uid"])
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return await service.log_wear(db, item, token["uid"], data)


@router.get("/items/{item_id}/wear-history", response_model=list[UsageLogResponse])
async def get_wear_history(
    item_id: int,
    limit: int = Query(default=20, le=100),
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_usage_logs(db, token["uid"], item_id=item_id, limit=limit)


# ── Semantic Search ─────────────────────────────────────────────────────────

@router.post("/search", response_model=list[WardrobeItemResponse])
async def semantic_search(
    req: SemanticSearchRequest,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    """Natural language search over wardrobe using CLIP text embeddings + pgvector."""
    from app.ai.clip_service import search_wardrobe
    results = await search_wardrobe(db, token["uid"], req.query, req.limit)
    return results
