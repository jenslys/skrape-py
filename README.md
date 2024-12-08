# skrape-py

A Python library for easily interacting with Skrape.ai API. Define your scraping schema using Pydantic and get type-safe results.

## Features

- 🛡️ **Type-safe**: Define your schemas using Pydantic and get fully typed results
- 🚀 **Simple API**: Just define a schema and get your data
- 🔄 **Async Support**: Built with async/await for efficient scraping
- 🧩 **Minimal Dependencies**: Built on top of proven libraries like Pydantic and httpx

## Installation

```bash
pip install skrape-py
```

Or with Poetry:

```bash
poetry add skrape-py
```

## Environment Setup

Setup your API key in `.env`:

```env
SKRAPE_API_KEY="your_api_key_here"
```

Get your API key on [Skrape.ai](https://skrape.ai)

## Quick Start

```python
from skrape import Skrape
from pydantic import BaseModel
from typing import List
import os
import asyncio

# Define your schema using Pydantic
class ProductSchema(BaseModel):
    title: str
    price: float
    description: str
    rating: float

async def main():
    # Use the client as an async context manager
    async with Skrape(api_key=os.getenv("SKRAPE_API_KEY")) as skrape:
        # Extract data
        response = await skrape.extract(
            "https://example.com/product",
            ProductSchema,
            {"render_js": True}  # Enable JavaScript rendering if needed
        )
        
        # Access the extracted data
        product = response.result
        print(f"Product: {product.title}")
        print(f"Price: ${product.price}")
        
        # Access rate limit information
        usage = response.usage
        print(f"Remaining credits: {usage.remaining}")
        print(f"Rate limit reset: {usage.rateLimit.reset}")

# Run the async function
asyncio.run(main())
```

## Schema Definition

We leverage Pydantic for defining schemas. Here's a more complex example:

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class Review(BaseModel):
    author: str
    rating: float = Field(ge=0, le=5)  # Rating between 0 and 5
    text: str
    date: str
    helpful_votes: Optional[int] = None

class ProductDetails(BaseModel):
    title: str
    price: float
    description: str
    rating: float
    reviews: List[Review]
    in_stock: bool
    shipping_info: Optional[str] = None
```

For a comprehensive understanding of all available options and advanced schema configurations, we recommend exploring [Pydantic's documentation](https://docs.pydantic.dev/).

## API Options

When calling `extract()`, you can pass additional options:

```python
response = await skrape.extract(
    url, 
    schema,
    {
        "render_js": True,  # Enable JavaScript rendering
        # Add other options as needed
    }
)
```

## Error Handling

The library provides typed exceptions for better error handling:

```python
from skrape import Skrape, SkrapeValidationError, SkrapeAPIError

async with Skrape(api_key=os.getenv("SKRAPE_API_KEY")) as skrape:
    try:
        response = await skrape.extract(url, schema)
    except SkrapeValidationError as e:
        # Schema validation failed
        print(f"Data doesn't match schema: {e}")
    except SkrapeAPIError as e:
        # API request failed (e.g., rate limit exceeded, invalid API key)
        print(f"API error: {e}")
```

## Rate Limiting

The API response includes rate limit information that you can use to manage your requests:

```python
response = await skrape.extract(url, schema)
usage = response.usage

print(f"Remaining credits: {usage.remaining}")
print(f"Rate limit info:")
print(f"  - Remaining: {usage.rateLimit.remaining}")
print(f"  - Base limit: {usage.rateLimit.baseLimit}")
print(f"  - Burst limit: {usage.rateLimit.burstLimit}")
print(f"  - Reset at: {usage.rateLimit.reset}")
```
