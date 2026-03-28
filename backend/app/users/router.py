from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.users import service
from app.users.schemas import (
    UserCreateOrSync,
    UserProfileUpdate,
    UserConsentUpdate,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/sync", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def sync_user(
    data: UserCreateOrSync,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    """Called immediately after Firebase login to create or sync the user record."""
    firebase_uid = token["uid"]
    user = await service.create_or_sync_user(db, firebase_uid, data)
    return user


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    user = await service.get_user_by_id(db, token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Call /users/sync first.")
    return user


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    updates: UserProfileUpdate,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    user = await service.get_user_by_id(db, token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return await service.update_user_profile(db, user, updates)


@router.put("/me/consent", response_model=UserProfileResponse)
async def update_consent(
    consent: UserConsentUpdate,
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    user = await service.get_user_by_id(db, token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return await service.update_consent(db, user, consent)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    token: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    """GDPR/NDPR: hard-delete all user data."""
    user = await service.get_user_by_id(db, token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await service.delete_user_data(db, user)
