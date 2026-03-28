"""
Sustainability Analytics
========================
Computes wardrobe usage statistics to promote conscious fashion habits.

Metrics:
  - wear_count per item
  - last_worn date per item
  - cost_per_wear (if purchase_cost set)
  - unworn_items (not worn in 30/60/90 days)
  - wardrobe_utilization_rate (items worn ≥1 / total active items)
  - outfit_repeat_rate (recommendations reused)
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.models.wardrobe import WardrobeItem
from app.models.usage_log import UsageLog

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ItemUsageStat(BaseModel):
    item_id: int
    item_name: str
    category: str
    wear_count: int
    last_worn: Optional[datetime]
    cost_per_wear: Optional[float]
    days_since_last_worn: Optional[int]


class WardrobeSummary(BaseModel):
    total_items: int
    items_worn_at_least_once: int
    utilization_rate: float  # 0.0 – 1.0
    unworn_30_days: int
    unworn_60_days: int
    unworn_90_days: int
    sustainability_score: int  # 0–100
    item_stats: list[ItemUsageStat]


@router.get("/summary", response_model=WardrobeSummary)
async def get_wardrobe_summary(
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = token["uid"]
    now = datetime.now(timezone.utc)

    # All active wardrobe items
    items_result = await db.execute(
        select(WardrobeItem).where(
            WardrobeItem.user_id == user_id,
            WardrobeItem.is_active == True,
        )
    )
    items = items_result.scalars().all()
    total_items = len(items)

    if total_items == 0:
        return WardrobeSummary(
            total_items=0,
            items_worn_at_least_once=0,
            utilization_rate=0.0,
            unworn_30_days=0,
            unworn_60_days=0,
            unworn_90_days=0,
            sustainability_score=0,
            item_stats=[],
        )

    # Wear counts + last worn per item
    logs_result = await db.execute(
        select(
            UsageLog.item_id,
            func.count(UsageLog.id).label("wear_count"),
            func.max(UsageLog.worn_at).label("last_worn"),
        )
        .where(UsageLog.user_id == user_id)
        .group_by(UsageLog.item_id)
    )
    logs_map = {row.item_id: row for row in logs_result.all()}

    item_stats = []
    worn_count = 0
    unworn_30 = unworn_60 = unworn_90 = 0

    for item in items:
        log = logs_map.get(item.id)
        wear_count = log.wear_count if log else 0
        last_worn = log.last_worn if log else None
        days_since = (now - last_worn).days if last_worn else None

        cost_per_wear = None
        if item.purchase_cost and wear_count > 0:
            cost_per_wear = round(item.purchase_cost / wear_count, 2)

        if wear_count > 0:
            worn_count += 1

        if last_worn is None or days_since >= 30:
            unworn_30 += 1
        if last_worn is None or days_since >= 60:
            unworn_60 += 1
        if last_worn is None or days_since >= 90:
            unworn_90 += 1

        item_stats.append(
            ItemUsageStat(
                item_id=item.id,
                item_name=item.name,
                category=item.category,
                wear_count=wear_count,
                last_worn=last_worn,
                cost_per_wear=cost_per_wear,
                days_since_last_worn=days_since,
            )
        )

    utilization_rate = round(worn_count / total_items, 2) if total_items else 0.0

    # Sustainability score (0–100)
    # Formula: utilization_rate × 70 + (1 - unworn_90/total) × 30
    sustainability_score = int(
        utilization_rate * 70 + (1 - min(unworn_90 / total_items, 1)) * 30
    )

    return WardrobeSummary(
        total_items=total_items,
        items_worn_at_least_once=worn_count,
        utilization_rate=utilization_rate,
        unworn_30_days=unworn_30,
        unworn_60_days=unworn_60,
        unworn_90_days=unworn_90,
        sustainability_score=sustainability_score,
        item_stats=sorted(item_stats, key=lambda x: x.wear_count, reverse=True),
    )


@router.get("/unworn", response_model=list[ItemUsageStat])
async def get_unworn_items(
    days: int = Query(default=30, ge=7, le=365),
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    """Return items not worn within the last N days."""
    user_id = token["uid"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Items with no log or last worn before cutoff
    worn_recently_result = await db.execute(
        select(UsageLog.item_id)
        .where(UsageLog.user_id == user_id, UsageLog.worn_at >= cutoff)
        .distinct()
    )
    recently_worn_ids = {row[0] for row in worn_recently_result.all()}

    all_items_result = await db.execute(
        select(WardrobeItem).where(
            WardrobeItem.user_id == user_id,
            WardrobeItem.is_active == True,
        )
    )
    all_items = all_items_result.scalars().all()

    stats = []
    for item in all_items:
        if item.id not in recently_worn_ids:
            stats.append(
                ItemUsageStat(
                    item_id=item.id,
                    item_name=item.name,
                    category=item.category,
                    wear_count=0,
                    last_worn=None,
                    cost_per_wear=None,
                    days_since_last_worn=None,
                )
            )
    return stats
