"""Cloudinary transformation and QR-code endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.user import User
from src.repository.photos import create_transform, get_photo_by_id, get_transform, list_transforms
from src.schemas.photo_transform import PhotoTransformResponse, TransformRequest
from src.services.cloudinary import transformed_url, transformation_type, validate_transformation
from src.services.dependencies import get_current_active_user
from src.services.permissions import can_modify_photo
from src.services.qr import generate_qr_code

router = APIRouter()


@router.post("/photos/{photo_id}/transform", response_model=PhotoTransformResponse, status_code=status.HTTP_201_CREATED)
async def create_photo_transform(
    photo_id: int, data: TransformRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)
):
    photo = await get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    if not can_modify_photo(photo.user_id, user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        validate_transformation(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    url = transformed_url(photo.public_id, data)
    qr_url = await generate_qr_code(url)
    item = await create_transform(
        db, photo_id=photo_id, transformation_type=transformation_type(data), transformed_url=url, qr_code_url=qr_url
    )
    await db.commit()
    return item


@router.get("/photos/{photo_id}/transforms", response_model=list[PhotoTransformResponse])
async def get_photo_transforms(photo_id: int, db: AsyncSession = Depends(get_db)):
    if await get_photo_by_id(db, photo_id) is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return await list_transforms(db, photo_id)


@router.get("/transforms/{transform_id}", response_model=PhotoTransformResponse)
async def get_transform_by_id(transform_id: int, db: AsyncSession = Depends(get_db)):
    item = await get_transform(db, transform_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Transformation not found")
    return item
