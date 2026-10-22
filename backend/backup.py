"""Backup completo de una cuenta (exportación JSON) y restauración sin pérdida.

La restauración nunca borra ni sobrescribe: crea registros nuevos con IDs
nuevos y omite pacientes y recetas que ya existen (mismo nombre, y para
pacientes también misma fecha de nacimiento), así importar dos veces el mismo
archivo no duplica datos. Los enlaces del portal no se exportan: restaurarlos
podría reactivar accesos que el profesional ya revocó. Los planes
alimenticios ("meal_plans") de backups antiguos se ignoran: el módulo se
reemplazó por las pautas.
"""
from datetime import date, datetime
from typing import Any, Dict, List

from sqlalchemy import Date, DateTime
from sqlalchemy.orm import Session

import models

BACKUP_VERSION = 2
_SKIP = {"id", "nutritionist_id", "patient_id", "receta_id"}


def _row(obj) -> Dict[str, Any]:
    out = {}
    for col in obj.__table__.columns:
        v = getattr(obj, col.name)
        out[col.name] = v.isoformat() if isinstance(v, (datetime, date)) else v
    return out


def _build(model, data: Dict[str, Any], **fks):
    """Instancia `model` con las columnas conocidas de `data` (ignora el resto)."""
    kwargs = {}
    for col in model.__table__.columns:
        if col.name in _SKIP or col.name not in data:
            continue
        v = data[col.name]
        if isinstance(v, str) and isinstance(col.type, DateTime):
            try:
                v = datetime.fromisoformat(v)
            except ValueError:
                v = None
        elif isinstance(v, str) and isinstance(col.type, Date):
            try:
                v = date.fromisoformat(v[:10])
            except ValueError:
                v = None
        kwargs[col.name] = v
    kwargs.update(fks)
    return model(**kwargs)


def export_patient(db: Session, user: models.Nutritionist, p: models.Patient) -> Dict[str, Any]:
    """Ficha completa de un paciente: datos, evaluaciones, pautas, antecedentes y citas."""
    pd = _row(p)
    pd["anthropometrics"] = [_row(a) for a in db.query(models.Anthropometric)
                             .filter(models.Anthropometric.patient_id == p.id).all()]
    pd["pautas"] = [_row(x) for x in db.query(models.Pauta).filter(models.Pauta.patient_id == p.id).all()]
    ant = db.query(models.Antecedentes).filter(models.Antecedentes.patient_id == p.id).first()
    pd["antecedentes"] = _row(ant) if ant else None
    pd["appointments"] = [_row(a) for a in db.query(models.Appointment).filter(
        models.Appointment.nutritionist_id == user.id, models.Appointment.patient_id == p.id).all()]
    return pd


def export_data(db: Session, user: models.Nutritionist) -> Dict[str, Any]:
    patients = db.query(models.Patient).filter(models.Patient.nutritionist_id == user.id).all()
    data: Dict[str, Any] = {
        "version": BACKUP_VERSION,
        "exported_at": datetime.utcnow().isoformat(),
        "nutritionist": {
            "id": user.id, "username": user.username, "email": user.email, "name": user.name,
            "clinic_name": user.clinic_name, "report_tagline": user.report_tagline,
            "logo_base64": user.logo_base64,
        },
        "patients": [],
        "recetas": [],
        "appointments_sin_paciente": [],
    }
    for p in patients:
        data["patients"].append(export_patient(db, user, p))

    for r in db.query(models.Receta).filter(models.Receta.nutritionist_id == user.id).all():
        rd = _row(r)
        rd["ingredientes"] = [_row(i) for i in db.query(models.RecetaIngrediente)
                              .filter(models.RecetaIngrediente.receta_id == r.id).all()]
        rd["equivalencias"] = [_row(e) for e in db.query(models.RecetaEquivalencia)
                               .filter(models.RecetaEquivalencia.receta_id == r.id).all()]
        data["recetas"].append(rd)

    data["appointments_sin_paciente"] = [_row(a) for a in db.query(models.Appointment).filter(
        models.Appointment.nutritionist_id == user.id, models.Appointment.patient_id.is_(None)).all()]
    return data


class BackupError(ValueError):
    pass


def restore_data(db: Session, user: models.Nutritionist, data: Dict[str, Any]) -> Dict[str, int]:
    if not isinstance(data, dict) or not isinstance(data.get("patients"), list):
        raise BackupError("El archivo no es un backup de NutriApp")
    version = data.get("version", 1)
    if version > BACKUP_VERSION:
        raise BackupError("El backup es de una versión más nueva de NutriApp")

    counts = {k: 0 for k in ("pacientes", "pacientes_omitidos", "evaluaciones", "pautas",
                             "antecedentes", "citas", "recetas", "recetas_omitidas")}
    existing = {(p.name or "", p.birth_date or "") for p in
                db.query(models.Patient).filter(models.Patient.nutritionist_id == user.id).all()}
    try:
        for pd in data["patients"]:
            key = (pd.get("name") or "", pd.get("birth_date") or "")
            if key in existing:
                counts["pacientes_omitidos"] += 1
                continue
            patient = _build(models.Patient, pd, nutritionist_id=user.id)
            db.add(patient)
            db.flush()
            existing.add(key)
            counts["pacientes"] += 1
            for a in pd.get("anthropometrics") or []:
                db.add(_build(models.Anthropometric, a, patient_id=patient.id))
                counts["evaluaciones"] += 1
            for pa in pd.get("pautas") or []:
                db.add(_build(models.Pauta, pa, patient_id=patient.id))
                counts["pautas"] += 1
            if pd.get("antecedentes"):
                db.add(_build(models.Antecedentes, pd["antecedentes"], patient_id=patient.id))
                counts["antecedentes"] += 1
            for ap in pd.get("appointments") or []:
                db.add(_build(models.Appointment, ap, nutritionist_id=user.id, patient_id=patient.id))
                counts["citas"] += 1

        recetas_existentes = {r.nombre for r in
                              db.query(models.Receta).filter(models.Receta.nutritionist_id == user.id).all()}
        for rd in data.get("recetas") or []:
            if rd.get("nombre") in recetas_existentes:
                counts["recetas_omitidas"] += 1
                continue
            receta = _build(models.Receta, rd, nutritionist_id=user.id)
            db.add(receta)
            db.flush()
            recetas_existentes.add(receta.nombre)
            for i in rd.get("ingredientes") or []:
                db.add(_build(models.RecetaIngrediente, i, receta_id=receta.id))
            for e in rd.get("equivalencias") or []:
                db.add(_build(models.RecetaEquivalencia, e, receta_id=receta.id))
            counts["recetas"] += 1

        for ap in data.get("appointments_sin_paciente") or []:
            db.add(_build(models.Appointment, ap, nutritionist_id=user.id, patient_id=None))
            counts["citas"] += 1
        db.commit()
    except BackupError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise BackupError(f"No se pudo restaurar el backup: {type(exc).__name__}") from exc
    return counts
