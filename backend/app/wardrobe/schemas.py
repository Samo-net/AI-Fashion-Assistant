from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

# Valid garment categories (Western + Nigerian traditional)
VALID_CATEGORIES = [
    "tops", "bottoms", "dress", "outerwear", "footwear", "accessories",
    "ankara", "agbada", "kaftan", "aso-oke", "lace", "senator",
    "iro-and-buba", "isiagu", "adire", "dashiki", "buba", "other",
]


class WardrobeItemCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    subcategory: Optional[str] = None
    primary_color: Optional[str] = None
    pattern: Optional[str] = None
    formality: Optional[str] = None
    image_url: Optional[str] = None
    image_s3_key: Optional[str] = None
    purchase_cost: Optional[float] = None
    attributes: Optional[dict[str, Any]] = {}


class WardrobeItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    subcategory: Optional[str] = None
    primary_color: Optional[str] = None
    pattern: Optional[str] = None
    formality: Optional[str] = None
    purchase_cost: Optional[float] = None
    attributes: Optional[dict[str, Any]] = None


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class WardrobeItemResponse(BaseModel):
    id: int
    user_id: str
    name: str
    category: str
    description: Optional[str]
    subcategory: Optional[str]
    primary_color: Optional[str]
    pattern: Optional[str]
    formality: Optional[str]
    image_url: Optional[str]
    purchase_cost: Optional[float]
    clip_processed: bool
    attributes: Optional[dict]
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PresignedUploadResponse(BaseModel):
    presigned_post: dict
    object_key: str
    public_url: str


class UsageLogCreate(BaseModel):
    occasion: Optional[str] = None
    notes: Optional[str] = None


class UsageLogResponse(BaseModel):
    id: int
    item_id: int
    occasion: Optional[str]
    notes: Optional[str]
    worn_at: datetime

    model_config = {"from_attributes": True}


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10
