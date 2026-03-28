from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.users.schemas import UserCreateOrSync, UserProfileUpdate, UserConsentUpdate
from datetime import datetime, timezone


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_or_sync_user(
    db: AsyncSession, firebase_uid: str, data: UserCreateOrSync
) -> User:
    """Create user on first login or return existing. Idempotent."""
    user = await get_user_by_id(db, firebase_uid)
    if user:
        # Sync display name / avatar from Firebase if not set
        if data.display_name and not user.display_name:
            user.display_name = data.display_name
        if data.avatar_url and not user.avatar_url:
            user.avatar_url = data.avatar_url
        await db.flush()
        return user

    user = User(
        id=firebase_uid,
        email=data.email,
        display_name=data.display_name,
        avatar_url=data.avatar_url,
        gdpr_consent=data.gdpr_consent,
        consent_timestamp=datetime.now(timezone.utc) if data.gdpr_consent else None,
    )
    db.add(user)
    await db.flush()
    return user


async def update_user_profile(
    db: AsyncSession, user: User, updates: UserProfileUpdate
) -> User:
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.flush()
    return user


async def update_consent(
    db: AsyncSession, user: User, consent: UserConsentUpdate
) -> User:
    user.gdpr_consent = consent.gdpr_consent
    if consent.gdpr_consent:
        user.consent_timestamp = datetime.now(timezone.utc)
    await db.flush()
    return user


async def delete_user_data(db: AsyncSession, user: User) -> None:
    """Hard delete — cascade removes wardrobe, recommendations, logs."""
    await db.delete(user)
    await db.flush()
