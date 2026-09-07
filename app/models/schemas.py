"""
Pydantic models describing exactly what shape each request body must have. Here,
FastAPI validates the incoming JSON against these models automatically and
returns a clean 422 error if it doesn't match, before your route code
even runs.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class SetRequest(BaseModel):
    value: Any = Field(..., description="Any JSON-serializable value")
    ttl: Optional[int] = Field(
        default=None, description="Time-to-live in seconds; omit for no expiry"
    )


class MSetRequest(BaseModel):
    items: dict[str, Any] = Field(
        ..., description="Multiple key/value pairs to set at once"
    )


class IncrRequest(BaseModel):
    amount: int = Field(
        default=1, description="Amount to increment by (can be negative)"
    )


class ExpireRequest(BaseModel):
    ttl: int = Field(..., description="Seconds until this key should expire")


class PublishRequest(BaseModel):
    message: dict[str, Any] = Field(
        ..., description="Arbitrary JSON payload to broadcast"
    )
