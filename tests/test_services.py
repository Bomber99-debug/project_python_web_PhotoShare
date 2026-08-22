import io
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from src.repository.blacklist import (add_to_blacklist, delete_expired, is_blacklisted,
                                      )
from src.schemas.photo_transform import (CropMode, ImageFormat, TransformRequest,
                                         )
from src.services import cloudinary as cloudinary_service, qr as qr_service
from src.services.security import (create_access_token, decode_access_token, hash_password, verify_password,
                                   )


def test_password_hashing():
	password = "Password123!"

	hashed = hash_password( password )

	assert hashed != password
	assert verify_password( password, hashed )
	assert not verify_password( "wrong-password", hashed )


def test_create_and_decode_access_token():
	token = create_access_token( { "sub": "123", "role": "user",
			}, )

	payload = decode_access_token( token )

	assert payload[ "sub" ] == "123"
	assert payload[ "role" ] == "user"
	assert "exp" in payload


def test_decode_invalid_access_token():
	with pytest.raises( ValueError ):
		decode_access_token( "invalid-token" )


def test_decode_expired_access_token():
	token = create_access_token( { "sub": "123", "role": "user",
			}, expires_delta=timedelta( seconds=-1 ), )

	with pytest.raises( ValueError ):
		decode_access_token( token )


def test_cloudinary_transformation_options():
	data = TransformRequest( width=400,
			height=300,
			crop=CropMode.FILL,
			angle=90,
			effect="sepia",
			format=ImageFormat.WEBP, )

	options = cloudinary_service.transformation_options( data )

	assert options == { "width": 400, "height": 300, "crop": "fill", "angle": 90, "effect": "sepia", "format": "webp",
			}


def test_cloudinary_transformation_type():
	data = TransformRequest( width=400, height=300, crop=CropMode.FILL, effect="sepia", )

	result = cloudinary_service.transformation_type( data )

	assert "w400" in result
	assert "h300" in result
	assert "c_fill" in result
	assert "e_sepia" in result


def test_cloudinary_auto_format_is_added_to_options():
	data = TransformRequest( format=ImageFormat.AUTO, )

	options = cloudinary_service.transformation_options( data )

	assert options == { "fetch_format": "auto",
			}

	cloudinary_service.validate_transformation( data )


def test_empty_transformation_is_invalid():
	data = TransformRequest()

	with pytest.raises( ValueError ):
		cloudinary_service.validate_transformation( data )


def test_valid_transformation():
	data = TransformRequest( width=100, )

	cloudinary_service.validate_transformation( data )


def test_cloudinary_configuration_requires_credentials( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service.settings, "cloudinary_name", "", )
	monkeypatch.setattr( cloudinary_service.settings, "cloudinary_api_key", "", )
	monkeypatch.setattr( cloudinary_service.settings, "cloudinary_api_secret", "", )

	with pytest.raises( HTTPException ) as exc:
		cloudinary_service._configure()

	assert exc.value.status_code == 500


def test_cloudinary_configuration( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service.settings, "cloudinary_name", "test-cloud", )
	monkeypatch.setattr( cloudinary_service.settings, "cloudinary_api_key", "test-key", )
	monkeypatch.setattr( cloudinary_service.settings, "cloudinary_api_secret", "test-secret", )

	called = { }

	def fake_config( **kwargs ):
		called.update( kwargs )

	monkeypatch.setattr( cloudinary_service.cloudinary, "config", fake_config, )

	cloudinary_service._configure()

	assert called[ "cloud_name" ] == "test-cloud"
	assert called[ "api_key" ] == "test-key"
	assert called[ "api_secret" ] == "test-secret"
	assert called[ "secure" ] is True


def test_transformed_url( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	def fake_cloudinary_url( public_id, **kwargs ):
		assert public_id == "photo-1"
		assert kwargs[ "width" ] == 300

		return ("https://example.com/transformed.jpg", { },
				)

	monkeypatch.setattr( cloudinary_service.cloudinary.utils, "cloudinary_url", fake_cloudinary_url, )

	result = cloudinary_service.transformed_url( "photo-1", TransformRequest( width=300, ), )

	assert result == "https://example.com/transformed.jpg"


async def test_upload_photo_service( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	def fake_upload( content, resource_type ):
		assert content == b"image-data"
		assert resource_type == "image"

		return { "secure_url": "https://example.com/image.jpg", "public_id": "photo-123",
				}

	monkeypatch.setattr( cloudinary_service.cloudinary.uploader, "upload", fake_upload, )

	file = UploadFile( file=io.BytesIO( b"image-data" ), filename="image.jpg", )

	result = await cloudinary_service.upload_photo( file )

	assert result == { "image_url": "https://example.com/image.jpg", "public_id": "photo-123",
			}


async def test_upload_empty_photo( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	file = UploadFile( file=io.BytesIO( b"" ), filename="empty.jpg", )

	with pytest.raises( HTTPException ) as exc:
		await cloudinary_service.upload_photo( file )

	assert exc.value.status_code == 400


async def test_cloudinary_upload_failure( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	def broken_upload( *args, **kwargs ):
		raise RuntimeError( "Cloudinary unavailable" )

	monkeypatch.setattr( cloudinary_service.cloudinary.uploader, "upload", broken_upload, )

	file = UploadFile( file=io.BytesIO( b"image" ), filename="image.jpg", )

	with pytest.raises( HTTPException ) as exc:
		await cloudinary_service.upload_photo( file )

	assert exc.value.status_code == 500
	assert exc.value.detail == "Failed to upload image to Cloudinary"


async def test_delete_cloudinary_photo( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	called = [ ]

	def fake_destroy( public_id, resource_type ):
		called.append( (public_id, resource_type,
				), )

	monkeypatch.setattr( cloudinary_service.cloudinary.uploader, "destroy", fake_destroy, )

	await cloudinary_service.delete_photo( "photo-123" )

	assert called == [ ("photo-123", "image",
			),
			]


async def test_delete_cloudinary_photo_failure( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	def broken_destroy( *args, **kwargs ):
		raise RuntimeError( "Cloudinary unavailable" )

	monkeypatch.setattr( cloudinary_service.cloudinary.uploader, "destroy", broken_destroy, )

	with pytest.raises( HTTPException ) as exc:
		await cloudinary_service.delete_photo( "photo-123" )

	assert exc.value.status_code == 500


async def test_upload_generated_image( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	def fake_upload( data, resource_type, folder, public_id, overwrite, ):
		assert data == b"png-data"
		assert resource_type == "image"
		assert folder == "photoshare/qrcodes"
		assert public_id == "qr-test"
		assert overwrite is True

		return { "secure_url": "https://example.com/qr.png",
				}

	monkeypatch.setattr( cloudinary_service.cloudinary.uploader, "upload", fake_upload, )

	result = await cloudinary_service.upload_image_bytes( b"png-data",
			folder="photoshare/qrcodes",
			public_id="qr-test", )

	assert result == "https://example.com/qr.png"


async def test_upload_generated_image_failure( monkeypatch, ):
	monkeypatch.setattr( cloudinary_service, "_configure", lambda: None, )

	def broken_upload( *args, **kwargs ):
		raise RuntimeError( "Upload failed" )

	monkeypatch.setattr( cloudinary_service.cloudinary.uploader, "upload", broken_upload, )

	with pytest.raises( HTTPException ) as exc:
		await cloudinary_service.upload_image_bytes( b"data", folder="test", public_id="test", )

	assert exc.value.status_code == 500


def test_create_qr_image():
	result = qr_service._create_qr_image( "https://example.com/photo.jpg", )

	assert isinstance( result, bytes )
	assert result.startswith( b"\x89PNG" )


async def test_generate_qr_code( monkeypatch, ):
	uploaded = { }

	async def fake_upload( data, *, folder, public_id, ):
		uploaded[ "data" ] = data
		uploaded[ "folder" ] = folder
		uploaded[ "public_id" ] = public_id

		return "https://example.com/generated-qr.png"

	monkeypatch.setattr( qr_service, "upload_image_bytes", fake_upload, )

	result = await qr_service.generate_qr_code( "https://example.com/photo.jpg", )

	assert result == "https://example.com/generated-qr.png"
	assert uploaded[ "folder" ] == "photoshare/qrcodes"
	assert uploaded[ "public_id" ].startswith( "qr_" )
	assert uploaded[ "data" ].startswith( b"\x89PNG" )


async def test_generate_qr_preserves_http_exception( monkeypatch, ):
	async def broken_upload( *args, **kwargs ):
		raise HTTPException( status_code=503, detail="Upload unavailable", )

	monkeypatch.setattr( qr_service, "upload_image_bytes", broken_upload, )

	with pytest.raises( HTTPException ) as exc:
		await qr_service.generate_qr_code( "https://example.com/photo.jpg", )

	assert exc.value.status_code == 503


async def test_generate_qr_generic_failure( monkeypatch, ):
	def broken_qr( *args, **kwargs ):
		raise RuntimeError( "QR failure" )

	monkeypatch.setattr( qr_service, "_create_qr_image", broken_qr, )

	with pytest.raises( HTTPException ) as exc:
		await qr_service.generate_qr_code( "https://example.com/photo.jpg", )

	assert exc.value.status_code == 500
	assert exc.value.detail == "Failed to generate QR code"


async def test_blacklist_repository( db_session, ):
	now = datetime.now( timezone.utc )

	assert await is_blacklisted( db_session, "missing-token", ) is False

	await add_to_blacklist( db_session, "expired-token", now - timedelta( minutes=1 ), )

	await add_to_blacklist( db_session, "active-token", now + timedelta( minutes=30 ), )

	await db_session.commit()

	assert await is_blacklisted( db_session, "expired-token", )

	assert await is_blacklisted( db_session, "active-token", )

	await delete_expired( db_session, now, )

	await db_session.commit()

	assert await is_blacklisted( db_session, "expired-token", ) is False

	assert await is_blacklisted( db_session, "active-token", ) is True