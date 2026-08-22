"""Cloudinary upload, deletion and transformation helpers."""

import asyncio

import cloudinary.uploader
import cloudinary.utils
from fastapi import HTTPException, UploadFile

import cloudinary
from src.conf.config import settings
from src.schemas.photo_transform import ImageFormat, TransformRequest


def _configure() -> None:
	if not all( [ settings.cloudinary_name, settings.cloudinary_api_key, settings.cloudinary_api_secret ] ):
		raise HTTPException( status_code=500, detail="Cloudinary is not configured" )
	cloudinary.config( cloud_name=settings.cloudinary_name,
	                   api_key=settings.cloudinary_api_key,
	                   api_secret=settings.cloudinary_api_secret,
	                   secure=True, )


def transformation_options( data: TransformRequest ) -> dict:
	options: dict = { }
	if data.width is not None:
		options[ "width" ] = data.width
	if data.height is not None:
		options[ "height" ] = data.height
	if data.crop is not None:
		options[ "crop" ] = data.crop.value
	if data.angle is not None:
		options[ "angle" ] = data.angle
	if data.effect is not None:
		options[ "effect" ] = data.effect
	if data.format == ImageFormat.AUTO:
		options[ "fetch_format" ] = "auto"
	elif data.format is not None:
		options[ "format" ] = data.format.value

	return options


def validate_transformation( data: TransformRequest ) -> None:
	if not transformation_options( data ):
		raise ValueError( "At least one transformation option is required" )


def transformation_type( data: TransformRequest ) -> str:
	parts: list[ str ] = [ ]
	if data.width is not None:
		parts.append( f"w{data.width}" )
	if data.height is not None:
		parts.append( f"h{data.height}" )
	if data.crop is not None:
		parts.append( f"c_{data.crop.value}" )
	if data.angle is not None:
		parts.append( f"a_{data.angle}" )
	if data.effect is not None:
		parts.append( f"e_{data.effect}" )
	if data.format is not None:
		parts.append( f"f_{data.format.value}" )
	return "_".join( parts )


def transformed_url( public_id: str, data: TransformRequest ) -> str:
	_configure()
	validate_transformation( data )
	url, _ = cloudinary.utils.cloudinary_url( public_id, secure=True, **transformation_options( data ) )
	return url


async def upload_photo( file: UploadFile ) -> dict[ str, str ]:
	_configure()
	content = await file.read()
	if not content:
		raise HTTPException( status_code=400, detail="Uploaded file is empty" )
	try:
		result = await asyncio.to_thread( cloudinary.uploader.upload, content, resource_type="image" )
	except Exception as exc:
		raise HTTPException( status_code=500, detail="Failed to upload image to Cloudinary" ) from exc
	return { "image_url": result[ "secure_url" ], "public_id": result[ "public_id" ] }


async def delete_photo( public_id: str ) -> None:
	_configure()
	try:
		await asyncio.to_thread( cloudinary.uploader.destroy, public_id, resource_type="image" )
	except Exception as exc:
		raise HTTPException( status_code=500, detail="Failed to delete image from Cloudinary" ) from exc


async def upload_image_bytes( data: bytes, *, folder: str, public_id: str ) -> str:
	_configure()
	try:
		result = await asyncio.to_thread( cloudinary.uploader.upload,
		                                  data,
		                                  resource_type="image",
		                                  folder=folder,
		                                  public_id=public_id,
		                                  overwrite=True, )
	except Exception as exc:
		raise HTTPException( status_code=500, detail="Failed to upload generated image" ) from exc
	return result[ "secure_url" ]
