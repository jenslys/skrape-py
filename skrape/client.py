from typing import TypeVar, Generic, Any, Dict, Optional, Union
import json
import httpx
from pydantic import BaseModel
from .errors import SkrapeAPIError, SkrapeValidationError

T = TypeVar("T", bound=BaseModel)

class RateLimit(BaseModel):
    """Rate limit information."""
    remaining: int
    baseLimit: int
    burstLimit: int
    reset: int

class UsageInfo(BaseModel):
    """Information about API usage and rate limits."""
    remaining: int
    rateLimit: RateLimit

class ExtractResponse(Generic[T]):
    """Response from the extract endpoint."""
    def __init__(self, result: T, usage: UsageInfo):
        self.result = result
        self.usage = usage

class Skrape(Generic[T]):
    """Client for interacting with the Skrape.ai API."""
    
    def __init__(self, api_key: str, base_url: str = "https://skrape.ai/api"):
        """Initialize the Skrape client.
        
        Args:
            api_key: Your Skrape.ai API key
            base_url: Base URL for the Skrape.ai API (default: https://skrape.ai/api)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=self.headers,
                verify=True,  # Verify SSL certificates
                timeout=30.0,  # 30 seconds timeout
                follow_redirects=True
            )
        return self.client

    async def extract(
        self, 
        url: str, 
        schema: type[T], 
        options: Optional[Dict[str, Any]] = None
    ) -> ExtractResponse[T]:
        """
        Extract data from a URL using the provided Pydantic schema.
        
        Args:
            url: The URL to scrape
            schema: A Pydantic model class defining the expected data structure
            options: Optional dictionary of scraping options (e.g., render_js)
            
        Returns:
            ExtractResponse containing the extracted data and usage information
            
        Raises:
            SkrapeAPIError: If the API request fails
            SkrapeValidationError: If the response doesn't match the schema
        """
        try:
            # Convert Pydantic schema to JSON Schema
            json_schema = schema.model_json_schema()
            
            # Prepare request payload
            payload = {
                "url": url,
                "schema": json_schema,
                "options": options or {}
            }
            
            # Make API request
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/extract",
                json=payload
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "10"))
                raise SkrapeAPIError(
                    f"Rate limit exceeded. Try again in {retry_after} seconds"
                )
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            try:
                result = schema.model_validate(data["result"])
                usage = UsageInfo.model_validate(data["usage"])
                return ExtractResponse(result=result, usage=usage)
            except Exception as e:
                raise SkrapeValidationError(f"Response validation failed: {str(e)}")
                
        except httpx.HTTPError as e:
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 401:
                    raise SkrapeAPIError("Invalid or missing API key")
                elif e.response.status_code == 503:
                    raise SkrapeAPIError("Server too busy, please retry")
            raise SkrapeAPIError(f"API request failed: {str(e)}")
            
    async def __aenter__(self):
        await self._get_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
            self.client = None
