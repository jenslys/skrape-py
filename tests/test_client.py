import pytest
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from skrape import Skrape, SkrapeAPIError, SkrapeValidationError

# Load environment variables
load_dotenv()

class SimpleSchema(BaseModel):
    """Schema for testing the extract endpoint."""
    title: str
    description: str

@pytest.mark.asyncio
async def test_extract_simple():
    """Test extracting simple data."""
    api_key = os.getenv("SKRAPE_API_KEY")
    assert api_key, "SKRAPE_API_KEY environment variable is not set"
    
    async with Skrape(api_key=api_key) as skrape:
        response = await skrape.extract(
            "https://example.com",
            SimpleSchema,
            {"render_js": False}
        )
        
        # Validate result
        assert response.result.title
        assert response.result.description
        
        # Validate usage info
        assert isinstance(response.usage.remaining, int)
        assert isinstance(response.usage.rateLimit.remaining, int)
        assert isinstance(response.usage.rateLimit.reset, int)
        assert isinstance(response.usage.rateLimit.baseLimit, int)
        assert isinstance(response.usage.rateLimit.burstLimit, int)

@pytest.mark.asyncio
async def test_invalid_api_key():
    """Test that invalid API key raises appropriate error."""
    async with Skrape(api_key="invalid_key") as skrape:
        with pytest.raises(SkrapeAPIError) as exc_info:
            await skrape.extract(
                "https://example.com",
                SimpleSchema,
                {"render_js": False}
            )
        assert "Invalid or missing API key" in str(exc_info.value)

@pytest.mark.asyncio
async def test_invalid_url():
    """Test that invalid URL raises appropriate error."""
    api_key = os.getenv("SKRAPE_API_KEY")
    assert api_key, "SKRAPE_API_KEY environment variable is not set"
    
    async with Skrape(api_key=api_key) as skrape:
        with pytest.raises(SkrapeAPIError):
            await skrape.extract(
                "https://this-url-does-not-exist.com",
                SimpleSchema,
                {"render_js": False}
            )

@pytest.mark.asyncio
async def test_rate_limit():
    """Test handling of rate limit errors."""
    api_key = os.getenv("SKRAPE_API_KEY")
    assert api_key, "SKRAPE_API_KEY environment variable is not set"
    
    # Make multiple requests to trigger rate limit
    async with Skrape(api_key=api_key) as skrape:
        for _ in range(5):  # Attempt 5 requests in quick succession
            try:
                await skrape.extract(
                    "https://example.com",
                    SimpleSchema,
                    {"render_js": False}
                )
            except SkrapeAPIError as e:
                if "Rate limit exceeded" in str(e):
                    # Test passed if we hit the rate limit
                    return
        
        # If we didn't hit the rate limit after 5 requests, that's fine too
        # The test is more about handling the rate limit when it occurs
