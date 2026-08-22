"""Pydantic schemas for photo ratings."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    value: int = Field(ge=1, le=5)


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    photo_id: int
    user_id: int
    value: int = Field(ge=1, le=5)
    created_at: datetime


class RatingAverageResponse(BaseModel):
    photo_id: int
    average_rating: float = Field(ge=0, le=5)
    ratings_count: int = Field(ge=0)
