import os
from pathlib import Path

# Must be set before `app.core.config.get_settings()` is first called anywhere
# (it's @lru_cache'd), so this happens at module import time, before any
# `from app...` import below.
os.environ.setdefault("LLM_MODE", "mock")
_TEST_DB_PATH = Path(__file__).parent / "test_carescribe.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.session import init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _clean_db_file():
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()
    yield
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()


@pytest_asyncio.fixture(autouse=True)
async def _init_db():
    await init_db()
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
