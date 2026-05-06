"""
NSFW / safety content filter for image generation prompts.
Blocks explicit, violent, or policy-violating prompts before they reach the API.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Blocked patterns (Russian + English, case-insensitive)
BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"(naked|nude|nudity|topless|nsfw)", re.I),
    re.compile(r"(porn|xxx|sex\s|sexual|erotic|fetish)", re.I),
    re.compile(r"(гол|обнаж|нюд|эротик|порно|секс\s|сексуальн)", re.I),
    re.compile(r"(gore|blood|violence|kill|murder|torture)", re.I),
    re.compile(r"(убийств|кров|насили|жесток|пытк|расчленён)", re.I),
    re.compile(r"(child|children|minor|underage|педофил|детск.*порно)", re.I),
    re.compile(r"(drug|cocaine|heroin|meth|наркотик|кокаин|героин|метамфетамин)", re.I),
    re.compile(r"(hate\s*speech|нацист|фашист|свастика|种族歧视)", re.I),
    re.compile(r"(bomb|explosive|террор|взрывн|бомб)", re.I),
]


class ContentFilter:
    """Filters unsafe prompts before image generation."""

    @staticmethod
    def is_safe(prompt: str) -> tuple[bool, str | None]:
        """
        Check if prompt is safe for generation.

        Returns:
            (True, None) if safe, (False, reason) if blocked.
        """
        for pattern in BLOCKED_PATTERNS:
            match = pattern.search(prompt)
            if match:
                reason = "Запрещённый контент"
                logger.warning("blocked prompt: word=%s prompt=%s", match.group(), prompt[:50])
                return False, reason

        return True, None
