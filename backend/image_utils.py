"""Validación de imágenes que suben los usuarios (logo del consultorio)."""
import base64
import binascii
import io
import re

from PIL import Image, UnidentifiedImageError

MAX_LOGO_BYTES = 500 * 1024
MAX_LOGO_SIDE = 800
_DATA_URI = re.compile(r"^data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\s]+)$")


def clean_logo(data_uri: str) -> str:
    """Valida el logo y lo devuelve re-codificado como PNG (data URI).

    Re-codificar con Pillow descarta metadatos y cualquier contenido que no sea
    la imagen en sí (archivos "políglotas", scripts en SVG, etc.). Solo se
    aceptan PNG, JPEG y WebP de hasta 500 KB.
    """
    m = _DATA_URI.match(data_uri.strip())
    if not m:
        raise ValueError("El logo debe ser una imagen PNG, JPEG o WebP")
    try:
        raw = base64.b64decode(m.group(2), validate=False)
    except (binascii.Error, ValueError):
        raise ValueError("El logo no es una imagen válida")
    if len(raw) > MAX_LOGO_BYTES:
        raise ValueError("El logo no puede superar 500 KB")
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
        img = Image.open(io.BytesIO(raw))
        if img.format not in ("PNG", "JPEG", "WEBP"):
            raise ValueError("El logo debe ser una imagen PNG, JPEG o WebP")
        if img.width * img.height > 25_000_000:
            raise ValueError("El logo es demasiado grande")
        img.thumbnail((MAX_LOGO_SIDE, MAX_LOGO_SIDE))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("El logo no es una imagen válida")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()
