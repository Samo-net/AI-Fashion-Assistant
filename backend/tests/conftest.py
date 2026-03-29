"""
Pytest configuration and shared fixtures.
Uses an in-memory SQLite database via aiosqlite for fast, isolated tests.
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.firebase import verify_firebase_token

# ── In-memory test database ────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSession() as session:
        yield session
        await session.rollback()


# ── Mock Firebase token ────────────────────────────────────────────────────
MOCK_USER_ID = "test-firebase-uid-001"
MOCK_TOKEN = {"uid": MOCK_USER_ID, "email": "test@example.com"}


def mock_verify_token():
    return MOCK_TOKEN


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP test client with dependency overrides for DB and Firebase."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_firebase_token] = mock_verify_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Get or create the test user — safe to call from multiple tests."""
    from app.models.user import User
    from sqlalchemy import select
    from datetime import datetime, timezone

    result = await db_session.execute(select(User).where(User.id == MOCK_USER_ID))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=MOCK_USER_ID,
            email="test@example.com",
            display_name="Test User",
            body_type="athletic",
            skin_tone="deep brown",
            style_preference="casual",
            city="Abuja",
            gdpr_consent=True,
            consent_timestamp=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_item(db_session, test_user):
    """Create a test wardrobe item."""
    from app.models.wardrobe import WardrobeItem

    item = WardrobeItem(
        user_id=MOCK_USER_ID,
        name="Blue Ankara Top",
        category="ankara",
        primary_color="blue",
        pattern="ankara print",
        formality="casual",
        image_url="https://example.com/top.jpg",
        clip_processed=False,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item
