"""Consentimiento del paciente para tratar sus datos de salud (Ley 19.628 / 21.719)."""
from datetime import datetime
from typing import Optional

from fastapi import Request

import models
from timeutil import utcnow

# Versión vigente de la política de privacidad (frontend: /privacidad)
CONSENT_VERSION = "2026-10"


def client_ip(request: Optional[Request]) -> Optional[str]:
    """IP real: el proxy de Railway la agrega al final de X-Forwarded-For."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()[:45]
    return request.client.host if request.client else None


def set_consent(patient: models.Patient, accepted: bool, source: str, request: Optional[Request] = None) -> None:
    """Registra o revoca el consentimiento; `source` es "profesional" o "portal". El llamador hace commit."""
    patient.consent_at = utcnow() if accepted else None
    patient.consent_version = CONSENT_VERSION if accepted else None
    patient.consent_source = source if accepted else None
    patient.consent_ip = client_ip(request) if accepted else None
