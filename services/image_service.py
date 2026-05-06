"""
Real image generation service.
DALL-E 3 (primary) → Flux Schnell (fallback).
"""
from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

IMAGE_COST = 1.0


class ImageGenerationError(Exception):
    pass


class ImageService:
    def __init__(
        self,
        openai_api_key: str,
        replicate_api_token: str,
        image_provider: str = "dalle",
        mock_mode: bool = False,
    ):
        self.openai_api_key = openai_api_key
        self.replicate_api_token = replicate_api_token
        self.image_provider = image_provider
        self.mock_mode = mock_mode

    async def generate(
        self, prompt: str, size: str = "1024x1024"
    ) -> dict:
        if self.mock_mode:
            await asyncio.sleep(1)
            return {
                "status": "success",
                "url": f"https://picsum.photos/seed/{hash(prompt) % 10000}/1024/1024",
                "cost": IMAGE_COST,
                "prompt": prompt,
            }
        if self.image_provider == "dalle" and self.openai_api_key:
            return await self._generate_dalle(prompt, size)
        if self.image_provider == "flux" and self.replicate_api_token:
            return await self._generate_flux(prompt)
        # fallback chain
        if self.openai_api_key:
            return await self._generate_dalle(prompt, size)
        if self.replicate_api_token:
            return await self._generate_flux(prompt)
        raise ImageGenerationError("No image provider configured")

    async def _generate_dalle(self, prompt: str, size: str) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": size,
                    "quality": "standard",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            url = data["data"][0]["url"]
            logger.info("dalle generated image: prompt=%s", prompt[:50])
            return {
                "status": "success",
                "url": url,
                "cost": IMAGE_COST,
                "prompt": prompt,
                "provider": "dalle",
            }

    async def _generate_flux(self, prompt: str) -> dict:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Bearer {self.replicate_api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "version": (
                        "black-forest-labs/flux-schnell"
                    ),
                    "input": {"prompt": prompt},
                },
            )
            resp.raise_for_status()
            prediction = resp.json()
            # Poll for completion
            get_url = prediction["urls"]["get"]
            for _ in range(30):
                await asyncio.sleep(2)
                poll = await client.get(
                    get_url,
                    headers={"Authorization": f"Bearer {self.replicate_api_token}"},
                )
                poll_data = poll.json()
                if poll_data["status"] == "succeeded":
                    url = poll_data["output"][0]
                    logger.info("flux generated image: prompt=%s", prompt[:50])
                    return {
                        "status": "success",
                        "url": url,
                        "cost": IMAGE_COST,
                        "prompt": prompt,
                        "provider": "flux",
                    }
                if poll_data["status"] == "failed":
                    raise ImageGenerationError(
                        f"Flux generation failed: {poll_data.get('error', 'unknown')}"
                    )
            raise ImageGenerationError("Flux generation timed out")
