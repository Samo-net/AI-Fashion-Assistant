from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.wardrobe import WardrobeItem, WardrobeTag, ItemTagAssociation
from app.models.usage_log import UsageLog
from app.wardrobe.schemas import WardrobeItemCreate, WardrobeItemUpdate, UsageLogCreate
from fastapi import HTTPException, status


async def _get_or_create_tag(db: AsyncSession, tag_name: str) -> WardrobeTag:
    result = await db.execute(select(WardrobeTag).where(WardrobeTag.name == tag_name.lower()))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = WardrobeTag(name=tag_name.lower())
        db.add(tag)
        await db.flush()
    return tag


async def get_item(db: AsyncSession, item_id: int, user_id: str) -> WardrobeItem | None:
    result = await db.execute(
        select(WardrobeItem)
        .options(selectinload(WardrobeItem.tags))
        .where(
            and_(
                WardrobeItem.id == item_id,
                WardrobeItem.user_id == user_id,
                WardrobeItem.is_active == True,
            )
        )
    )
    return result.scalar_one_or_none()


async def list_items(
    db: AsyncSession,
    user_id: str,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[WardrobeItem]:
    query = (
        select(WardrobeItem)
        .options(selectinload(WardrobeItem.tags))
        .where(and_(WardrobeItem.user_id == user_id, WardrobeItem.is_active == True))
        .order_by(WardrobeItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if category:
        query = query.where(WardrobeItem.category == category)
    result = await db.execute(query)
    return result.scalars().all()


async def create_item(
    db: AsyncSession, user_id: str, data: WardrobeItemCreate
) -> WardrobeItem:
    item = WardrobeItem(
        user_id=user_id,
        **data.model_dump(exclude={"attributes"} if data.attributes is None else {}),
    )
    db.add(item)
    await db.flush()
    return item


async def update_item(
    db: AsyncSession, item: WardrobeItem, updates: WardrobeItemUpdate
) -> WardrobeItem:
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.flush()
    return item


async def delete_item(db: AsyncSession, item: WardrobeItem) -> None:
    item.is_active = False  # Soft delete — preserves usage logs
    await db.flush()


async def add_tags_to_item(
    db: AsyncSession, item: WardrobeItem, tag_names: list[str]
) -> WardrobeItem:
    for name in tag_names:
        tag = await _get_or_create_tag(db, name)
        if tag not in item.tags:
            item.tags.append(tag)
    await db.flush()
    return item


async def log_wear(
    db: AsyncSession, item: WardrobeItem, user_id: str, data: UsageLogCreate
) -> UsageLog:
    log = UsageLog(item_id=item.id, user_id=user_id, **data.model_dump())
    db.add(log)
    await db.flush()
    return log


async def get_usage_logs(
    db: AsyncSession, user_id: str, item_id: int | None = None, limit: int = 50
) -> list[UsageLog]:
    query = (
        select(UsageLog)
        .where(UsageLog.user_id == user_id)
        .order_by(UsageLog.worn_at.desc())
        .limit(limit)
    )
    if item_id:
        query = query.where(UsageLog.item_id == item_id)
    result = await db.execute(query)
    return result.scalars().all()
