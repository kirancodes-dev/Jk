"""
Measures how much the upload pipeline shrinks photos before storage
(storage_service.strip_image_metadata: orientation fix, metadata removal,
longest edge capped at IMAGE_MAX_DIMENSION, JPEG re-encode).

Without arguments it generates six deterministic photo-like JPEGs at a common
phone-camera size (4032 x 3024, quality 92, with camera and GPS EXIF). These
are synthetic: real photos compress differently, so pass a folder of real
evidence photos to measure those instead.

Run:
  PYTHONPATH=. python scripts/image_storage_benchmark.py
  PYTHONPATH=. python scripts/image_storage_benchmark.py --photos path/to/jpegs
"""
import argparse
import io
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

from backend.app.core.config import settings  # noqa: E402
from backend.app.services.storage_service import storage_service  # noqa: E402

PHONE_SIZE = (4032, 3024)


def synthetic_photo(seed: int) -> bytes:
    """Smooth shapes plus sensor-like grain, saved the way a phone camera would."""
    rng = random.Random(seed)
    w, h = PHONE_SIZE
    small = Image.new("RGB", (w // 8, h // 8))
    draw = ImageDraw.Draw(small)
    for y in range(small.height):  # sky-to-ground gradient
        t = y / small.height
        draw.line([(0, y), (small.width, y)], fill=(int(120 + 80 * t), int(160 - 40 * t), int(210 - 150 * t)))
    for _ in range(60):  # buildings, trees, people, water
        x0, y0 = rng.randrange(small.width), rng.randrange(small.height)
        x1, y1 = x0 + rng.randrange(10, 160), y0 + rng.randrange(10, 120)
        shape = draw.ellipse if rng.random() < 0.5 else draw.rectangle
        shape([x0, y0, x1, y1], fill=tuple(rng.randrange(256) for _ in range(3)))
    img = small.resize(PHONE_SIZE, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    grain = Image.effect_noise(PHONE_SIZE, 12).convert("RGB")
    img = Image.blend(img, grain, 0.12)

    exif = Image.Exif()
    exif[0x010F], exif[0x0110] = "PhoneMaker", "Model X"
    exif[0x8825] = {1: "N", 2: (23.0, 20.0, 39.0), 3: "E", 4: (85.0, 18.0, 35.0)}
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, exif=exif.tobytes())
    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--photos", type=Path, help="folder of real JPEG photos to measure")
    args = parser.parse_args()

    if args.photos:
        samples = [(p.name, p.read_bytes()) for p in sorted(args.photos.glob("*.jp*g"))]
        label = f"real photos in {args.photos}"
    else:
        samples = [(f"synthetic-{i}.jpg", synthetic_photo(i)) for i in range(6)]
        label = f"synthetic {PHONE_SIZE[0]}x{PHONE_SIZE[1]} photo-like JPEGs (quality 92)"
    if not samples:
        sys.exit("No JPEG files found.")

    print(f"IMAGE_MAX_DIMENSION={settings.IMAGE_MAX_DIMENSION}, "
          f"IMAGE_JPEG_QUALITY={settings.IMAGE_JPEG_QUALITY}; {label}")
    total_in = total_out = 0
    for name, raw in samples:
        out = storage_service.strip_image_metadata(raw, "image/jpeg")
        before, after = Image.open(io.BytesIO(raw)).size, Image.open(io.BytesIO(out)).size
        total_in, total_out = total_in + len(raw), total_out + len(out)
        print(f"  {name:<18} {before[0]}x{before[1]} {len(raw) / 1e6:6.2f} MB -> "
              f"{after[0]}x{after[1]} {len(out) / 1e6:6.2f} MB  ({(1 - len(out) / len(raw)) * 100:4.1f}% smaller)")
    n = len(samples)
    print(f"Average: {total_in / n / 1e6:.2f} MB -> {total_out / n / 1e6:.2f} MB per photo "
          f"({(1 - total_out / total_in) * 100:.1f}% less storage)")


if __name__ == "__main__":
    main()
