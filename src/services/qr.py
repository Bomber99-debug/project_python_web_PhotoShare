"""QR-code generation for transformed image links."""

import asyncio
import hashlib
import io

import qrcode
from fastapi import HTTPException

from src.services.cloudinary import upload_image_bytes


def _create_qr_image(url: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def generate_qr_code(url: str) -> str:
    try:
        image = await asyncio.to_thread(_create_qr_image, url)
        digest = hashlib.sha256(url.encode()).hexdigest()[:16]
        return await upload_image_bytes(image, folder="photoshare/qrcodes", public_id=f"qr_{digest}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate QR code") from exc
