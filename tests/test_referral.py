"""
Tests for referral service.
"""
from __future__ import annotations

import pytest

from models import Database
from services.referral_service import REFERRAL_BONUS, WELCOME_BONUS, ReferralService


@pytest.fixture
def db():
    d = Database("sqlite+aiosqlite:///:memory:")
    # use sync for pytest setup
    import asyncio
    asyncio.run(d.create_tables())
    return d


@pytest.mark.asyncio
async def test_referral_link_generation():
    svc = ReferralService(db=None)  # type: ignore
    link = svc.generate_referral_link("test_bot", "abc123")
    assert "t.me/test_bot" in link
    assert "ref_abc123" in link


@pytest.mark.asyncio
async def test_get_or_create_user_with_referral(db: Database):
    # Create referrer first
    referrer = await db.get_or_create_user(
        telegram_id=100,
        username="referrer",
        full_name="Referrer User",
    )

    # Create new user with referral code
    new_user = await db.get_or_create_user(
        telegram_id=200,
        username="referee",
        full_name="Referee User",
        referral_code_from=referrer.referral_code,
    )

    # New user should have welcome bonus
    assert new_user.balance >= WELCOME_BONUS
    assert new_user.referred_by == referrer.id

    # Referrer should have gotten bonus
    ref_updated = await db.get_user_by_telegram_id(100)
    assert ref_updated is not None
    assert ref_updated.balance >= REFERRAL_BONUS


@pytest.mark.asyncio
async def test_self_referral_not_allowed(db: Database):
    user = await db.get_or_create_user(
        telegram_id=300,
        username="selfref",
        full_name="Self Referrer",
    )
    # Try to use own code
    user2 = await db.get_or_create_user(
        telegram_id=301,
        username="selfref2",
        full_name="Self Referrer 2",
        referral_code_from=user.referral_code,
    )
    # Should not link to self since user2 referred_by points to user
    assert user2.referred_by is not None
    assert user2.referred_by == user.id  # valid referral

    # Try creating user with invalid referral code
    user3 = await db.get_or_create_user(
        telegram_id=302,
        username="invalidref",
        full_name="Invalid",
        referral_code_from="nonexistent",
    )
    assert user3.referred_by is None  # no referrer


@pytest.mark.asyncio
async def test_get_or_create_user_no_referral(db: Database):
    user = await db.get_or_create_user(
        telegram_id=400,
        username="noref",
        full_name="No Referral",
    )
    assert user.referred_by is None
    assert user.balance >= WELCOME_BONUS
