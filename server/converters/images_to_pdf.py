from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from converters.base import ConversionContext, ConversionError, ConversionResult

MAX_DIMENSION = 10_000
MAX_PIXELS = 50_000_000
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF"}


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    try:
        with Image.open(input_path) as probe:
            if probe.format not in ALLOWED_FORMATS:
                raise ConversionError("This image format is not supported.")
            probe.verify()
    except ConversionError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise ConversionError("This image could not be read.") from exc

    try:
        with Image.open(input_path) as opened:
            image = ImageOps.exif_transpose(opened)
            width, height = image.size
            if width > MAX_DIMENSION or height > MAX_DIMENSION or width * height > MAX_PIXELS:
                raise ConversionError("This image is too large to convert safely.")

            if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")

            output = context.workdir / "result.pdf"
            image.save(output, "PDF", resolution=150.0, quality=85)
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError("This image could not be converted.") from exc

    return ConversionResult(path=output, media_type="application/pdf", extension="pdf")
