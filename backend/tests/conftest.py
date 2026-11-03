import os
import sys
import pytest_asyncio

# Ensure backend directory is in sys.path regardless of working directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.session import engine  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def dispose_db_engine_between_tests():
    yield
    await engine.dispose()
