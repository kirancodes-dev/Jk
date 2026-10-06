"""
Uploaded photos are stored upright, without metadata, and at most
IMAGE_MAX_DIMENSION px on the longest edge (docs/SUSTAINABILITY_AND_COST.md).
"""
import io

from PIL import Image

from backend.app.core.config import settings
from backend.app.services.storage_service import storage_service

GPS_IFD = 0x8825
ORIENTATION = 0x0112


def _jpeg(size, orientation=None, gps=False, quality=92):
    img = Image.effect_noise(size, 40).convert("RGB")
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"
    if orientation:
        exif[ORIENTATION] = orientation
    if gps:
        exif[GPS_IFD] = {1: "N", 2: (23.0, 20.0, 39.0), 3: "E", 4: (85.0, 18.0, 35.0)}
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, exif=exif.tobytes())
    return buf.getvalue()


def test_gps_and_camera_metadata_are_removed():
    raw = _jpeg((640, 480), gps=True)
    assert Image.open(io.BytesIO(raw)).getexif().get_ifd(GPS_IFD)

    cleaned = Image.open(io.BytesIO(storage_service.strip_image_metadata(raw, "image/jpeg")))
    exif = cleaned.getexif()
    assert not exif.get_ifd(GPS_IFD)
    assert 0x010F not in exif


def test_exif_orientation_is_applied_before_metadata_is_dropped():
    # Orientation 6 = the camera was held in portrait; viewers rotate 90° clockwise.
    raw = _jpeg((300, 200), orientation=6)
    cleaned = Image.open(io.BytesIO(storage_service.strip_image_metadata(raw, "image/jpeg")))
    assert cleaned.size == (200, 300)
    assert ORIENTATION not in cleaned.getexif()


def test_phone_photo_is_downscaled_and_smaller():
    raw = _jpeg((4032, 3024))
    out = storage_service.strip_image_metadata(raw, "image/jpeg")
    img = Image.open(io.BytesIO(out))
    assert max(img.size) == settings.IMAGE_MAX_DIMENSION
    assert img.size == (2048, 1536)
    assert len(out) < len(raw)


def test_small_images_keep_their_size():
    raw = _jpeg((800, 600))
    img = Image.open(io.BytesIO(storage_service.strip_image_metadata(raw, "image/jpeg")))
    assert img.size == (800, 600)


def test_png_with_transparency_is_downscaled():
    img = Image.new("RGBA", (3000, 1000), (0, 120, 60, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out = Image.open(io.BytesIO(storage_service.strip_image_metadata(buf.getvalue(), "image/png")))
    assert out.size == (2048, 683)
    assert out.mode == "RGBA"


def test_non_images_are_untouched():
    pdf = b"%PDF-1.4\n%fake\n"
    assert storage_service.strip_image_metadata(pdf, "application/pdf") == pdf
