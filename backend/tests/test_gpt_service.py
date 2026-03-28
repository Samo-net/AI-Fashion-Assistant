"""
Unit tests for the GPT-4o recommendation prompt builder and response parser.
All OpenAI API calls are mocked.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# ── Season detection ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("month,expected", [
    (11, "harmattan"),
    (12, "harmattan"),
    (1,  "harmattan"),
    (2,  "harmattan"),
    (3,  "dry season"),
    (4,  "dry season"),
    (5,  "rainy season"),
    (8,  "rainy season"),
    (10, "rainy season"),
])
def test_determine_nigerian_season(month, expected):
    from app.ai.gpt_service import _determine_nigerian_season
    assert _determine_nigerian_season(month) == expected


# ── Wardrobe list builder ────────────────────────────────────────────────────

def test_build_wardrobe_list_includes_all_fields():
    from app.ai.gpt_service import _build_wardrobe_list

    item = MagicMock()
    item.id = 42
    item.name = "Blue Ankara Top"
    item.category = "ankara"
    item.primary_color = "blue"
    item.pattern = "ankara print"
    item.formality = "casual"

    result = _build_wardrobe_list([item])
    assert "42" in result
    assert "Blue Ankara Top" in result
    assert "ankara" in result
    assert "blue" in result


def test_build_wardrobe_list_handles_missing_fields():
    from app.ai.gpt_service import _build_wardrobe_list

    item = MagicMock()
    item.id = 1
    item.name = "Mystery Item"
    item.category = "other"
    item.primary_color = None
    item.pattern = None
    item.formality = None

    result = _build_wardrobe_list([item])
    assert "unknown color" in result
    assert "no pattern" in result
    assert "unspecified" in result


def test_build_wardrobe_list_empty():
    from app.ai.gpt_service import _build_wardrobe_list
    assert _build_wardrobe_list([]) == "No items available."


# ── Context hash ─────────────────────────────────────────────────────────────

def test_context_hash_is_deterministic():
    from app.ai.gpt_service import build_context_hash
    h1 = build_context_hash("user-1", "church", 28.5, "harmattan")
    h2 = build_context_hash("user-1", "church", 28.5, "harmattan")
    assert h1 == h2


def test_context_hash_differs_by_occasion():
    from app.ai.gpt_service import build_context_hash
    h1 = build_context_hash("user-1", "church", 28.0, "harmattan")
    h2 = build_context_hash("user-1", "casual", 28.0, "harmattan")
    assert h1 != h2


def test_context_hash_is_16_chars():
    from app.ai.gpt_service import build_context_hash
    h = build_context_hash("uid", "work", 30.0, "dry season")
    assert len(h) == 16


# ── generate_recommendation (mocked GPT-4o) ──────────────────────────────────

async def test_generate_recommendation_parses_response():
    from app.ai.gpt_service import generate_recommendation

    mock_user = MagicMock()
    mock_user.body_type = "athletic"
    mock_user.skin_tone = "deep brown"
    mock_user.style_preference = "casual"
    mock_user.city = "Abuja"

    mock_item = MagicMock()
    mock_item.id = 5
    mock_item.name = "White Kaftan"
    mock_item.category = "kaftan"
    mock_item.primary_color = "white"
    mock_item.pattern = "solid color"
    mock_item.formality = "traditional"

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        '{"item_ids": [5], "rationale": "Perfect for a casual Friday.",'
        '"accessory_suggestion": "Brown leather sandals", "outfit_description": "White kaftan"}'
    )

    with patch("app.ai.gpt_service.get_openai_client") as mock_client, \
         patch("app.ai.gpt_service.get_weather", new_callable=AsyncMock, return_value={"temp": 30, "condition": "clear sky"}):
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await generate_recommendation(mock_user, [mock_item], "casual")

    assert result["item_ids"] == [5]
    assert "rationale" in result
    assert result["season"] in ("harmattan", "rainy season", "dry season")


async def test_generate_recommendation_filters_invalid_item_ids():
    """item_ids returned by GPT that don't exist in wardrobe should be stripped."""
    from app.ai.gpt_service import generate_recommendation

    mock_user = MagicMock()
    mock_user.body_type = "slim"
    mock_user.skin_tone = "caramel"
    mock_user.style_preference = "formal"
    mock_user.city = "Lagos"

    mock_item = MagicMock()
    mock_item.id = 10

    mock_response = MagicMock()
    # GPT hallucinates item ID 999 which doesn't exist
    mock_response.choices[0].message.content = (
        '{"item_ids": [10, 999], "rationale": "Nice outfit.",'
        '"accessory_suggestion": "Watch", "outfit_description": "Suit"}'
    )

    with patch("app.ai.gpt_service.get_openai_client") as mock_client, \
         patch("app.ai.gpt_service.get_weather", new_callable=AsyncMock, return_value={"temp": 27, "condition": "cloudy"}):
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await generate_recommendation(mock_user, [mock_item], "work")

    assert 999 not in result["item_ids"]
    assert 10 in result["item_ids"]


# ── System prompt quality ────────────────────────────────────────────────────

def test_system_prompt_mentions_nigerian_fashion():
    from app.ai.gpt_service import SYSTEM_PROMPT
    assert "Nigerian" in SYSTEM_PROMPT
    assert "Ankara" in SYSTEM_PROMPT or "Agbada" in SYSTEM_PROMPT


def test_prompt_template_includes_all_context_fields():
    from app.ai.gpt_service import RECOMMENDATION_PROMPT_TEMPLATE
    for field in ["{body_type}", "{skin_tone}", "{occasion}", "{weather_temp}", "{season}", "{wardrobe_list}"]:
        assert field in RECOMMENDATION_PROMPT_TEMPLATE, f"Missing field: {field}"
