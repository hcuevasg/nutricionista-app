"""Helpers for circular patient photo display."""
import os
from pathlib import Path

FOTOS_DIR = Path(__file__).parent.parent / "fotos"


def ensure_fotos_dir() -> Path:
    FOTOS_DIR.mkdir(exist_ok=True)
    return FOTOS_DIR


def get_initials(name: str) -> str:
    parts = name.strip().split()
    if not parts:
        return "?"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def make_circle_image(photo_path, size: int, initials: str = "?"):
    """Return CTkImage with circular crop. Falls back to green initials avatar."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import customtkinter as ctk

        if photo_path and os.path.isfile(str(photo_path)):
            base = Image.open(photo_path).convert("RGBA")
            w, h = base.size
            s = min(w, h)
            base = base.crop(((w - s) // 2, (h - s) // 2,
                               (w - s) // 2 + s, (h - s) // 2 + s))
        else:
            S = 200
            base = Image.new("RGBA", (S, S), (26, 107, 60, 255))
            draw = ImageDraw.Draw(base)
            font_size = 80
            font = None
            for fname in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
                try:
                    font = ImageFont.truetype(fname, font_size)
                    break
                except Exception:
                    pass
            if font is None:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), initials, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((S - tw) / 2 - bbox[0], (S - th) / 2 - bbox[1]),
                      initials, fill="white", font=font)

        base = base.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(base, mask=mask)
        return ctk.CTkImage(result, size=(size, size))
    except Exception:
        return None


def make_circle_pil(photo_path, size: int):
    """Return PIL RGBA Image with circular crop (for PDF). Returns None if no photo."""
    try:
        from PIL import Image, ImageDraw
        if not photo_path or not os.path.isfile(str(photo_path)):
            return None
        base = Image.open(photo_path).convert("RGBA")
        w, h = base.size
        s = min(w, h)
        base = base.crop(((w - s) // 2, (h - s) // 2,
                           (w - s) // 2 + s, (h - s) // 2 + s))
        base = base.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        result = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        result.paste(base, mask=mask)
        return result
    except Exception:
        return None
