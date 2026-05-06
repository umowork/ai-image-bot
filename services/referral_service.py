"""
Referral service.
"""
from __future__ import annotations

import logging

from models import Database, User

logger = logging.getLogger(__name__)

REFERRAL_BONUS = 5.0  # credits awarded to referrer
WELCOME_BONUS = 10.0  # credits for new user signup


class ReferralService:
    def __init__(self, db: Database):
        self.db = db

    async def process_referral(
        self, user: User, referral_code: str
    ) -> dict:
        """Process referral: find referrer, award bonus."""
        if user.referred_by:
            return {"success": False, "reason": "already_referred"}

        if user.referral_code == referral_code:
            return {"success": False, "reason": "self_referral"}

        # find referrer by code
        referrer = await self.db.get_user_by_referral_code(referral_code)
        if not referrer:
            return {"success": False, "reason": "invalid_code"}

        # this is handled in get_or_create_user, but for completeness:
        return {
            "success": True,
            "referrer_id": referrer.id,
            "bonus": REFERRAL_BONUS,
        }

    def generate_referral_link(
        self, bot_username: str, referral_code: str
    ) -> str:
        return f"https://t.me/{bot_username}?start=ref_{referral_code}"
