from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.core.redis import get_redis
from app.core.config import settings
from app.models.recommendation import Recommendation
from app.models.wardrobe import WardrobeItem
from app.users.service import get_user_by_id
from app.recommendations.schemas import (
    RecommendationRequest,
    RecommendationFeedback,
    RecommendationResponse,
)
from app.ai.gpt_service import generate_recommendation, build_context_hash
import json

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    req: RecommendationRequest,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    user = await get_user_by_id(db, token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Fetch active wardrobe items
    result = await db.execute(
        select(WardrobeItem).where(
            WardrobeItem.user_id == user.id,
            WardrobeItem.is_active == True,
        )
    )
    wardrobe = result.scalars().all()
    if not wardrobe:
        raise HTTPException(status_code=400, detail="Add clothing items to your wardrobe first.")

    # Check Redis cache
    weather_data = None
    context_hash = None
    if req.use_weather:
        from app.ai.gpt_service import get_weather
        weather_data = await get_weather(user.city or "Abuja")

    from datetime import datetime
    month = datetime.now().month
    from app.ai.gpt_service import _determine_nigerian_season
    season = _determine_nigerian_season(month)
    context_hash = build_context_hash(
        user.id, req.occasion, weather_data["temp"] if weather_data else 28, season
    )
    cache_key = f"rec:{context_hash}"
    cached = await redis.get(cache_key)
    if cached:
        cached_id = int(cached)
        result = await db.execute(
            select(Recommendation).where(Recommendation.id == cached_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Generate new recommendation
    output = await generate_recommendation(user, wardrobe, req.occasion, weather_data)

    rec = Recommendation(
        user_id=user.id,
        occasion=req.occasion,
        weather_condition=output["weather"]["condition"],
        weather_temp_celsius=output["weather"]["temp"],
        season=output["season"],
        item_ids=output["item_ids"],
        rationale=output.get("rationale"),
        accessory_suggestion=output.get("accessory_suggestion"),
        gpt_model_used=output.get("gpt_model_used"),
        context_hash=context_hash,
    )
    db.add(rec)
    await db.flush()

    # Cache for TTL
    await redis.setex(cache_key, settings.RECOMMENDATION_CACHE_TTL, str(rec.id))

    return rec


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.user_id == token["uid"])
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.put("/{rec_id}/feedback", response_model=RecommendationResponse)
async def submit_feedback(
    rec_id: int,
    feedback: RecommendationFeedback,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == rec_id,
            Recommendation.user_id == token["uid"],
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    if feedback.accepted is not None:
        rec.accepted = feedback.accepted
    if feedback.user_rating is not None:
        if not 1 <= feedback.user_rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
        rec.user_rating = feedback.user_rating
    await db.flush()
    return rec
