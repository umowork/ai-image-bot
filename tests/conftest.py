"""
Shared test fixtures.
"""
from __future__ import annotations

import pytest_asyncio

from models import Database


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database with tables created."""
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_tables()
    return database
