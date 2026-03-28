"""
GPT-4o Recommendation Service
==============================
Builds structured prompts from user context + wardrobe, calls GPT-4o,
parses the JSON response, and returns outfit suggestions.

Nigerian cultural context (seasons, occasions, traditional attire) is
baked into the system prompt.
"""

import hashlib
import json
import logging
from typing import Optional

from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """You are an expert fashion stylist with deep knowledge of Nigerian and West African fashion.
You are fluent in both traditional Nigerian styles (Ankara, Agbada, Kaftan, Aso-oke, Senator suits, Iro and Buba, Isiagu, Adire, Dashiki) and contemporary Western fashion.
You understand the Nigerian climate (harmattan, rainy season, dry season) and social occasions (church, weddings, traditional ceremonies, work, casual outings).
Your role is to suggest outfit combinations that are culturally appropriate, stylish, and practical for the user's context.
Always return valid JSON. Do not include markdown code blocks in your response.
"""

RECOMMENDATION_PROMPT_TEMPLATE = """User Profile:
- Body type: {body_type}
- Skin tone: {skin_tone}
- Style preference: {style_preference}
- Location: {city}, Nigeria

Current Context:
- Occasion: {occasion}
- Weather: {weather_temp}°C, {weather_condition}
- Season: {season}

Available wardrobe items (ID | Name | Category | Color | Pattern | Formality):
{wardrobe_list}

Task: Suggest one complete outfit from the available items above.

Return ONLY a JSON object with this exact structure:
{{
  "item_ids": [list of integer item IDs to include],
  "rationale": "2-3 sentence friendly explanation of why this outfit works for the occasion and user",
  "accessory_suggestion": "One accessory suggestion (may or may not be in their wardrobe)",
  "outfit_description": "A concise description of the full outfit for visualization (e.g. 'Deep blue Ankara top with white linen trousers and brown leather sandals')"
}}
"""


def _determine_nigerian_season(month: int) -> str:
    """Map calendar month to Nigerian season."""
    if month in (11, 12, 1, 2):
        return "harmattan"
    elif month in (3, 4):
        return "dry season"
    elif month in (5, 6, 7, 8, 9, 10):
        return "rainy season"
    return "dry season"


def _build_wardrobe_list(items: list) -> str:
    lines = []
    for item in items:
        lines.append(
            f"{item.id} | {item.name} | {item.category} | "
            f"{item.primary_color or 'unknown color'} | "
            f"{item.pattern or 'no pattern'} | "
            f"{item.formality or 'unspecified'}"
        )
    return "\n".join(lines) if lines else "No items available."


def build_context_hash(user_id: str, occasion: str, weather_temp: float, season: str) -> str:
    raw = f"{user_id}:{occasion}:{round(weather_temp or 0)}:{season}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def get_weather(city: str) -> dict:
    """Fetch current weather for a Nigerian city from OpenWeatherMap."""
    import aiohttp
    if not settings.OPENWEATHER_API_KEY:
        return {"temp": 28, "condition": "clear sky"}  # fallback for dev
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city},NG&appid={settings.OPENWEATHER_API_KEY}&units=metric"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "temp": data["main"]["temp"],
                    "condition": data["weather"][0]["description"],
                }
    return {"temp": 28, "condition": "clear sky"}


async def generate_recommendation(
    user,
    wardrobe_items: list,
    occasion: str,
    override_weather: Optional[dict] = None,
) -> dict:
    """
    Build prompt, call GPT-4o, parse response.
    Returns parsed dict with item_ids, rationale, accessory_suggestion, outfit_description.
    """
    from datetime import datetime

    weather = override_weather or await get_weather(user.city or "Abuja")
    month = datetime.now().month
    season = _determine_nigerian_season(month)

    wardrobe_list = _build_wardrobe_list(wardrobe_items)

    prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(
        body_type=user.body_type or "not specified",
        skin_tone=user.skin_tone or "not specified",
        style_preference=user.style_preference or "mixed",
        city=user.city or "Abuja",
        occasion=occasion,
        weather_temp=weather["temp"],
        weather_condition=weather["condition"],
        season=season,
        wardrobe_list=wardrobe_list,
    )

    client = get_openai_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=500,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    # Validate item_ids are all ints and exist in the wardrobe
    valid_ids = {item.id for item in wardrobe_items}
    parsed["item_ids"] = [i for i in parsed.get("item_ids", []) if i in valid_ids]

    return {
        **parsed,
        "weather": weather,
        "season": season,
        "gpt_model_used": settings.OPENAI_MODEL,
    }
