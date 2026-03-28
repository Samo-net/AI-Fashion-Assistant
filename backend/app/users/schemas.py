from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    body_type: Optional[str] = None  # slim, athletic, curvy, plus-size, petite
    skin_tone: Optional[str] = None  # deep brown, caramel, ebony, warm brown, light brown
    style_preference: Optional[str] = None  # casual, traditional, formal, smart-casual, mix
    city: Optional[str] = None
    state: Optional[str] = None
    avatar_url: Optional[str] = None


class UserConsentUpdate(BaseModel):
    gdpr_consent: bool


class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    body_type: Optional[str]
    skin_tone: Optional[str]
    style_preference: Optional[str]
    city: Optional[str]
    state: Optional[str]
    gdpr_consent: bool
    consent_timestamp: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreateOrSync(BaseModel):
    """Called on first login to create or sync user from Firebase token."""
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gdpr_consent: bool = False
