"""Utilidades HTTP compartidas por los routers."""
import unicodedata
from urllib.parse import quote


def attachment(filename: str) -> dict:
    """Header Content-Disposition que admite tildes (RFC 6266 / 5987).

    Los headers HTTP van en latin-1: con "María" o "Comparación" en el nombre la
    respuesta fallaba. Se envía un nombre ASCII de respaldo más filename* en UTF-8.
    """
    ascii_name = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode() or "archivo"
    ascii_name = ascii_name.replace('"', "")
    return {"Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"}
