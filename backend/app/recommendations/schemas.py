from pydantic import BaseModel
from typing import Optional
from datetime import datetime


VALID_OCCASIONS = [
    "casual", "work", "church", "wedding-guest", "traditional-ceremony",
    "date", "party", "sports", "travel", "formal-event",
]


class RecommendationRequest(BaseModel):
    occasion: str = "casual"
    use_weather: bool = True


class RecommendationFeedback(BaseModel):
    accepted: Optional[bool] = None
    user_rating: Optional[int] = None  # 1-5


class RecommendationResponse(BaseModel):
    id: int
    occasion: Optional[str]
    weather_condition: Optional[str]
    weather_temp_celsius: Optional[float]
    season: Optional[str]
    item_ids: list[int]
    rationale: Optional[str]
    accessory_suggestion: Optional[str]
    gpt_model_used: Optional[str]
    accepted: Optional[bool]
    user_rating: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
