"""Audit logging utility."""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Request
import models


def log(
    db: Session,
    action: str,
    resource: str,
    nutritionist_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    detail: Optional[str] = None,
    request: Optional[Request] = None,
):
    ip = None
    if request:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None

    entry = models.AuditLog(
        nutritionist_id=nutritionist_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()
