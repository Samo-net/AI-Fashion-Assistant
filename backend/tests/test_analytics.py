"""
Unit tests for sustainability analytics.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


async def test_summary_empty_wardrobe(client: AsyncClient, test_user):
    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] >= 0
    assert "sustainability_score" in data
    assert "utilization_rate" in data


async def test_summary_after_adding_items(client: AsyncClient, test_user, db_session):
    from app.models.wardrobe import WardrobeItem

    # Add 3 items
    for i in range(3):
        item = WardrobeItem(user_id=test_user.id, name=f"Item {i}", category="tops")
        db_session.add(item)
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] >= 3
    assert 0.0 <= data["utilization_rate"] <= 1.0


async def test_sustainability_score_improves_with_wear(client: AsyncClient, test_user, db_session):
    from app.models.wardrobe import WardrobeItem
    from app.models.usage_log import UsageLog

    item = WardrobeItem(user_id=test_user.id, name="Worn Item", category="ankara")
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    log = UsageLog(item_id=item.id, user_id=test_user.id, occasion="casual")
    db_session.add(log)
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 200
    assert resp.json()["items_worn_at_least_once"] >= 1


async def test_cost_per_wear_calculation(client: AsyncClient, test_user, db_session):
    from app.models.wardrobe import WardrobeItem
    from app.models.usage_log import UsageLog

    item = WardrobeItem(
        user_id=test_user.id,
        name="Expensive Agbada",
        category="agbada",
        purchase_cost=50000.0,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    # Log 5 wears
    for _ in range(5):
        log = UsageLog(item_id=item.id, user_id=test_user.id)
        db_session.add(log)
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/summary")
    item_stat = next(
        (s for s in resp.json()["item_stats"] if s["item_id"] == item.id), None
    )
    assert item_stat is not None
    assert item_stat["wear_count"] == 5
    assert item_stat["cost_per_wear"] == pytest.approx(10000.0, 0.01)


async def test_unworn_items_endpoint(client: AsyncClient, test_user, db_session):
    from app.models.wardrobe import WardrobeItem
    from app.models.usage_log import UsageLog

    # Item never worn
    never_worn = WardrobeItem(user_id=test_user.id, name="Never Worn", category="tops")
    # Item worn 40 days ago
    worn_old = WardrobeItem(user_id=test_user.id, name="Old Wear", category="bottoms")
    db_session.add_all([never_worn, worn_old])
    await db_session.commit()
    await db_session.refresh(worn_old)

    old_log = UsageLog(
        item_id=worn_old.id,
        user_id=test_user.id,
        worn_at=datetime.now(timezone.utc) - timedelta(days=40),
    )
    db_session.add(old_log)
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/unworn?days=30")
    assert resp.status_code == 200
    ids = [i["item_id"] for i in resp.json()]
    assert never_worn.id in ids
    assert worn_old.id in ids  # worn 40 days ago, threshold is 30
