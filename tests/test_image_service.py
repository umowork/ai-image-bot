"""
Tests for image service.
"""
from __future__ import annotations

import pytest
import respx
from httpx import Response

from services.image_service import IMAGE_COST, ImageService


@pytest.mark.asyncio
async def test_generate_mock_mode():
    svc = ImageService(
        openai_api_key="",
        replicate_api_token="",
        mock_mode=True,
    )
    result = await svc.generate("test prompt")
    assert result["status"] == "success"
    assert "picsum.photos" in result["url"]
    assert result["cost"] == IMAGE_COST


@pytest.mark.asyncio
async def test_generate_dalle_success():
    svc = ImageService(
        openai_api_key="sk-test",
        replicate_api_token="",
        image_provider="dalle",
    )
    with respx.mock:
        route = respx.post("https://api.openai.com/v1/images/generations").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {"url": "https://oaidalleapiprodscus.blob.core.windows.net/test"}
                    ]
                },
            )
        )
        result = await svc.generate("cat in space")
        assert route.called
        assert result["status"] == "success"
        assert "test" in result["url"]
        assert result["provider"] == "dalle"


@pytest.mark.asyncio
async def test_generate_dalle_failure():
    svc = ImageService(
        openai_api_key="sk-test",
        replicate_api_token="",
        image_provider="dalle",
    )
    with respx.mock:
        respx.post("https://api.openai.com/v1/images/generations").mock(
            return_value=Response(401, text="Unauthorized")
        )
        with pytest.raises(Exception) as exc:
            await svc.generate("test")
        assert "401" in str(exc.value)


@pytest.mark.asyncio
async def test_generate_no_provider_configured():
    svc = ImageService(
        openai_api_key="",
        replicate_api_token="",
        mock_mode=False,
    )
    with pytest.raises(Exception) as exc:
        await svc.generate("test")
    assert "No image provider configured" in str(exc.value)
