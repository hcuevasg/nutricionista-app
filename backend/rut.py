"""RUT chileno: normalización y dígito verificador (módulo 11)."""
import re
from typing import Optional

_CLEAN = re.compile(r"[^0-9kK]")


def compute_dv(body: str) -> str:
    """Dígito verificador por módulo 11: se multiplica el cuerpo de derecha a
    izquierda por la serie 2,3,4,5,6,7 (repetida), se suma y se calcula 11 - (suma mod 11);
    11 → '0' y 10 → 'K'."""
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    dv = 11 - total % 11
    return "0" if dv == 11 else "K" if dv == 10 else str(dv)


def normalize(value: str) -> Optional[str]:
    """'12.345.678-k' → '12345678-K' si el RUT es válido; None si no lo es."""
    raw = _CLEAN.sub("", value or "").upper()
    if len(raw) < 2:
        return None
    body, dv = raw[:-1], raw[-1]
    if not body.isdigit() or not 100_000 <= int(body) <= 99_999_999:
        return None
    body = str(int(body))   # sin ceros a la izquierda
    return f"{body}-{dv}" if compute_dv(body) == dv else None


def format_rut(normalized: Optional[str]) -> Optional[str]:
    """'12345678-K' → '12.345.678-K'."""
    if not normalized:
        return normalized
    body, dv = normalized.split("-")
    return f"{int(body):,}".replace(",", ".") + f"-{dv}"
