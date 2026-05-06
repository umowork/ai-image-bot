"""
Smoke test: end-to-end with all mocked HTTP.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_db_crud():
    """Full CRUD cycle for database."""
    from models import Database

    db = Database("sqlite+aiosqlite:///:memory:")
    await db.create_tables()

    # Create user
    user = await db.get_or_create_user(
        telegram_id=1000, username="smoke", full_name="Smoke Test"
    )
    assert user.telegram_id == 1000
    assert user.balance == 10.0  # welcome bonus

    # Add generation
    gen = await db.add_generation(user.id, "image", "test prompt", 1.0)
    assert gen.status == "pending"

    # Update generation
    await db.update_generation(gen.id, "https://example.com/img.png", "done")
    # Re-fetch to verify update
    gens = await db.get_user_generations(user.id)
    assert len(gens) == 1
    assert gens[0].result_url == "https://example.com/img.png"
    assert gens[0].status == "done"

    # Check history
    gens = await db.get_user_generations(user.id)
    assert len(gens) == 1
    assert gens[0].result_url == "https://example.com/img.png"

    # Deduct balance
    await db.deduct_balance(user.id, 2.0)
    updated = await db.get_user_by_telegram_id(1000)
    assert updated is not None
    assert updated.balance == 8.0


@pytest.mark.asyncio
async def test_referral_flow():
    """Full referral flow: referrer creates link → new user joins → both get bonuses."""
    from models import Database

    db = Database("sqlite+aiosqlite:///:memory:")
    await db.create_tables()

    referrer = await db.get_or_create_user(
        telegram_id=2000, username="referrer", full_name="Referrer"
    )
    initial_balance = referrer.balance

    new_user = await db.get_or_create_user(
        telegram_id=2001,
        username="newbie",
        full_name="New User",
        referral_code_from=referrer.referral_code,
    )

    # Check new user has welcome bonus
    assert new_user.balance >= 10.0
    # Check referrer got bonus
    ref_updated = await db.get_user_by_telegram_id(2000)
    assert ref_updated is not None
    assert ref_updated.balance > initial_balance


@pytest.mark.asyncio
async def test_database_stats():
    """Stats aggregation works."""
    from models import Database

    db = Database("sqlite+aiosqlite:///:memory:")
    await db.create_tables()

    # Create users
    for i in range(3):
        await db.get_or_create_user(
            telegram_id=3000 + i,
            username=f"user{i}",
            full_name=f"User {i}",
        )

    stats = await db.get_stats()
    assert stats["users"] >= 3
