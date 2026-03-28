from httpx import AsyncClient


async def test_list_items_empty(client: AsyncClient, test_user):
    resp = await client.get("/api/v1/wardrobe/items")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_create_item(client: AsyncClient, test_user):
    resp = await client.post(
        "/api/v1/wardrobe/items",
        json={"name": "White Senator Suit", "category": "senator", "formality": "formal"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "White Senator Suit"
    assert data["category"] == "senator"
    assert data["clip_processed"] is False


async def test_get_item(client: AsyncClient, test_item):
    resp = await client.get(f"/api/v1/wardrobe/items/{test_item.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Blue Ankara Top"


async def test_get_item_wrong_user_returns_404(client: AsyncClient, test_item, db_session):
    """Item belonging to another user should return 404."""
    from app.models.wardrobe import WardrobeItem
    other_item = WardrobeItem(
        user_id="different-user-uid",
        name="Private Item",
        category="tops",
    )
    db_session.add(other_item)
    await db_session.commit()
    await db_session.refresh(other_item)

    resp = await client.get(f"/api/v1/wardrobe/items/{other_item.id}")
    assert resp.status_code == 404


async def test_update_item(client: AsyncClient, test_item):
    resp = await client.put(
        f"/api/v1/wardrobe/items/{test_item.id}",
        json={"primary_color": "navy", "formality": "smart-casual"},
    )
    assert resp.status_code == 200
    assert resp.json()["primary_color"] == "navy"


async def test_delete_item(client: AsyncClient, test_user):
    # Create and delete
    create = await client.post(
        "/api/v1/wardrobe/items",
        json={"name": "Temp Item", "category": "tops"},
    )
    item_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/wardrobe/items/{item_id}")
    assert delete.status_code == 204

    # Should be gone
    get = await client.get(f"/api/v1/wardrobe/items/{item_id}")
    assert get.status_code == 404


async def test_log_wear(client: AsyncClient, test_item):
    resp = await client.post(
        f"/api/v1/wardrobe/items/{test_item.id}/wear",
        json={"occasion": "church", "notes": "Sunday service"},
    )
    assert resp.status_code == 201
    assert resp.json()["occasion"] == "church"


async def test_wear_history(client: AsyncClient, test_item):
    # Log two wears first
    for occ in ["casual", "work"]:
        await client.post(f"/api/v1/wardrobe/items/{test_item.id}/wear", json={"occasion": occ})

    resp = await client.get(f"/api/v1/wardrobe/items/{test_item.id}/wear-history")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_list_items_by_category(client: AsyncClient, test_user):
    # Create items in two categories
    await client.post("/api/v1/wardrobe/items", json={"name": "Agbada Set", "category": "agbada"})
    await client.post("/api/v1/wardrobe/items", json={"name": "White Tee", "category": "tops"})

    resp = await client.get("/api/v1/wardrobe/items?category=agbada")
    assert resp.status_code == 200
    assert all(i["category"] == "agbada" for i in resp.json())
