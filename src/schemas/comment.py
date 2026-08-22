"""Pydantic schemas for photo comments."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Comment text cannot be empty")
    return value


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _clean_text(value)


class CommentUpdate(CommentCreate):
    pass


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    photo_id: int
    user_id: int
    text: str
    created_at: datetime
    updated_at: datetime
