"""
Unit tests for the CLIP classification pipeline.
All model calls are mocked — these tests verify the classification logic,
label bank integrity, and embedding search routing, not PyTorch internals.
"""

import pytest
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock


# ── Label bank tests ────────────────────────────────────────────────────────

def test_category_labels_include_nigerian_garments():
    from app.ai.clip_service import CATEGORY_LABELS
    nigerian_terms = ["ankara dress", "agbada", "senator suit", "kaftan", "isiagu", "adire fabric"]
    for term in nigerian_terms:
        assert term in CATEGORY_LABELS, f"Missing Nigerian label: {term}"


def test_pattern_labels_include_nigerian_patterns():
    from app.ai.clip_service import PATTERN_LABELS
    assert "ankara print" in PATTERN_LABELS
    assert "adire pattern" in PATTERN_LABELS
    assert "lace pattern" in PATTERN_LABELS


def test_color_labels_cover_full_spectrum():
    from app.ai.clip_service import COLOR_LABELS
    assert len(COLOR_LABELS) >= 10
    assert "black" in COLOR_LABELS
    assert "white" in COLOR_LABELS
    assert "multicolor" in COLOR_LABELS


def test_formality_labels_include_traditional_occasions():
    from app.ai.clip_service import FORMALITY_LABELS
    assert "traditional ceremony outfit" in FORMALITY_LABELS
    assert "religious service wear" in FORMALITY_LABELS
    assert "wedding guest outfit" in FORMALITY_LABELS


# ── cosine_top1 logic ───────────────────────────────────────────────────────

def test_cosine_top1_returns_highest_similarity():
    from app.ai.clip_service import _cosine_top1
    embedding = np.array([1.0, 0.0, 0.0])
    label_embeddings = np.array([
        [0.0, 1.0, 0.0],   # label 0 — orthogonal
        [0.9, 0.1, 0.0],   # label 1 — very similar (normalized below)
        [0.0, 0.0, 1.0],   # label 2 — orthogonal
    ])
    # Normalize label embeddings
    norms = np.linalg.norm(label_embeddings, axis=1, keepdims=True)
    label_embeddings = label_embeddings / norms

    result = _cosine_top1(embedding, label_embeddings)
    assert result == 1  # label 1 is most similar


def test_cosine_top1_handles_tied_scores():
    from app.ai.clip_service import _cosine_top1
    embedding = np.array([1.0, 0.0])
    labels = np.array([[1.0, 0.0], [1.0, 0.0]])  # identical embeddings
    result = _cosine_top1(embedding, labels)
    assert result in (0, 1)  # either is acceptable for a tie


# ── classify_and_embed (mocked) ─────────────────────────────────────────────

async def test_classify_and_embed_returns_correct_keys():
    mock_embedding = np.random.rand(512).astype(np.float32)
    mock_embedding /= np.linalg.norm(mock_embedding)

    with patch("app.ai.clip_service._fetch_image", new_callable=AsyncMock) as mock_fetch, \
         patch("app.ai.clip_service._encode_image", return_value=mock_embedding), \
         patch("app.ai.clip_service._cosine_top1", side_effect=[0, 0, 0, 0]), \
         patch("app.ai.clip_service._label_embeddings", {
             "category": np.random.rand(len(__import__("app.ai.clip_service", fromlist=["CATEGORY_LABELS"]).CATEGORY_LABELS), 512),
             "color": np.random.rand(5, 512),
             "pattern": np.random.rand(5, 512),
             "formality": np.random.rand(5, 512),
         }):
        from app.ai.clip_service import classify_and_embed
        from PIL import Image as PILImage
        mock_fetch.return_value = PILImage.new("RGB", (224, 224))

        result = await classify_and_embed("https://example.com/img.jpg")

    assert "embedding" in result
    assert "category" in result
    assert "primary_color" in result
    assert "pattern" in result
    assert "formality" in result
    assert len(result["embedding"]) == 512


async def test_classify_and_embed_handles_http_error():
    with patch("app.ai.clip_service._fetch_image", side_effect=Exception("HTTP 404")):
        from app.ai.clip_service import classify_and_embed
        with pytest.raises(Exception, match="HTTP 404"):
            await classify_and_embed("https://bad-url.example.com/img.jpg")


# ── Nigerian-label accuracy smoke test (offline) ────────────────────────────

def test_nigerian_label_count_is_sufficient():
    """Ensures the label bank has enough Nigerian entries to be meaningful."""
    from app.ai.clip_service import CATEGORY_LABELS
    nigerian_count = sum(
        1 for label in CATEGORY_LABELS
        if any(term in label for term in ["ankara", "agbada", "kaftan", "iro", "isiagu", "adire", "dashiki", "senator", "buba", "lace"])
    )
    assert nigerian_count >= 10, f"Only {nigerian_count} Nigerian labels — add more for bias coverage"
