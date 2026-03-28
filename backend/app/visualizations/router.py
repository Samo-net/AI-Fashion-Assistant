import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.core.config import settings
from app.models.visualization import VisualizationJob
from app.models.recommendation import Recommendation
from app.models.wardrobe import WardrobeItem
from app.users.service import get_user_by_id

router = APIRouter(prefix="/visualizations", tags=["visualizations"])


class VisualizationRequest(BaseModel):
    recommendation_id: int


class VisualizationResponse(BaseModel):
    id: str
    status: str
    image_url: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


async def _run_visualization_job(job_id: str, user_id: str, db_session_factory):
    """Background task: run SD generation and update job status."""
    from app.ai.sd_service import generate_visualization

    async with db_session_factory() as db:
        try:
            result = await db.execute(
                select(VisualizationJob).where(VisualizationJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            if not job:
                return

            job.status = "processing"
            await db.flush()

            payload = job.input_payload or {}
            output = await generate_visualization(
                job_id=job_id,
                user_id=user_id,
                outfit_description=payload.get("outfit_description", "stylish outfit"),
                item_image_urls=payload.get("item_image_urls", []),
                skin_tone=payload.get("skin_tone"),
            )

            job.status = "completed"
            job.image_url = output["image_url"]
            job.image_s3_key = output["image_s3_key"]
            job.positive_prompt = output["positive_prompt"]
            job.negative_prompt = output["negative_prompt"]
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            await db.rollback()
            async with db_session_factory() as db2:
                result = await db2.execute(
                    select(VisualizationJob).where(VisualizationJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    await db2.commit()


@router.post("", response_model=VisualizationResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_visualization(
    req: VisualizationRequest,
    background_tasks: BackgroundTasks,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Enforce daily limit
    from sqlalchemy import cast, Date
    today_count_result = await db.execute(
        select(func.count(VisualizationJob.id)).where(
            VisualizationJob.user_id == token["uid"],
            cast(VisualizationJob.created_at, Date) == func.current_date(),
        )
    )
    today_count = today_count_result.scalar()
    if today_count >= settings.MAX_VISUALIZATIONS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Daily visualization limit ({settings.MAX_VISUALIZATIONS_PER_DAY}) reached.",
        )

    # Load recommendation + item images
    rec_result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == req.recommendation_id,
            Recommendation.user_id == token["uid"],
        )
    )
    rec = rec_result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    # Collect image URLs from recommended items
    item_results = await db.execute(
        select(WardrobeItem).where(WardrobeItem.id.in_(rec.item_ids))
    )
    items = item_results.scalars().all()
    image_urls = [i.image_url for i in items if i.image_url]

    outfit_desc = (rec.rationale or "stylish Nigerian outfit")[:200]

    job_id = str(uuid.uuid4())
    job = VisualizationJob(
        id=job_id,
        recommendation_id=rec.id,
        user_id=token["uid"],
        status="queued",
        input_payload={
            "outfit_description": outfit_desc,
            "item_image_urls": image_urls,
            "skin_tone": user.skin_tone,
        },
    )
    db.add(job)
    await db.flush()

    from app.core.database import AsyncSessionLocal
    background_tasks.add_task(
        _run_visualization_job, job_id, token["uid"], AsyncSessionLocal
    )

    return job


@router.get("/{job_id}", response_model=VisualizationResponse)
async def get_visualization_status(
    job_id: str,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VisualizationJob).where(
            VisualizationJob.id == job_id,
            VisualizationJob.user_id == token["uid"],
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Visualization job not found.")
    return job
