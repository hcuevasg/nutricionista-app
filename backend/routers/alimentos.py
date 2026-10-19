"""Búsqueda de alimentos: base local (con alimentos chilenos) y USDA como respaldo."""
import os
import unicodedata
from typing import List

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

router = APIRouter(prefix="/alimentos", tags=["alimentos"])

USDA_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
USDA_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
MAX_RESULTS = 15

# Nutrient IDs en FoodData Central
_NID = {
    1008: "calorias",        # Energy (kcal)
    1003: "proteinas_g",     # Protein
    1005: "carbohidratos_g", # Carbohydrate, by difference
    1004: "grasas_g",        # Total lipid (fat)
    1079: "fibra_g",         # Fiber, total dietary
}


def normalize(text: str) -> str:
    """Minúsculas y sin tildes: "Plátano" → "platano"."""
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def seed_alimentos(db: Session) -> int:
    """Carga la base integrada si la tabla está vacía. Devuelve cuántos insertó."""
    if db.query(models.Alimento.id).first():
        return 0
    from data.alimentos_base import ALIMENTOS_CHILENOS, ALIMENTOS_GENERALES
    rows = [(r, "base") for r in ALIMENTOS_GENERALES] + [(r, "chile") for r in ALIMENTOS_CHILENOS]
    for (nombre, nombre_en, kcal, prot, cho, grasa, fibra), fuente in rows:
        db.add(models.Alimento(
            nombre=nombre, nombre_en=nombre_en, nombre_norm=normalize(f"{nombre} {nombre_en or ''}"),
            calorias_100g=kcal, proteinas_100g=prot, carbohidratos_100g=cho,
            grasas_100g=grasa, fibra_100g=fibra, fuente=fuente,
        ))
    db.commit()
    return len(rows)


def _local_to_dict(a: models.Alimento) -> dict:
    return {
        "fdcId": None, "id": a.id, "nombre": a.nombre, "fuente": a.fuente,
        "calorias_100g": a.calorias_100g, "proteinas_100g": a.proteinas_100g,
        "carbohidratos_100g": a.carbohidratos_100g, "grasas_100g": a.grasas_100g,
        "fibra_100g": a.fibra_100g,
    }


def _parse_food(food: dict):
    """Convierte un food dict de USDA al formato interno (por 100g)."""
    nutrientes = {v: 0.0 for v in _NID.values()}
    for fn in food.get("foodNutrients", []):
        nid = fn.get("nutrientId") or fn.get("nutrientNumber")
        val = fn.get("value") or fn.get("amount") or 0
        if nid in _NID:
            nutrientes[_NID[nid]] = round(float(val), 2)

    return {
        "fdcId":            food.get("fdcId"),
        "nombre":           food.get("description", ""),
        "fuente":           "usda",
        "calorias_100g":    nutrientes["calorias"],
        "proteinas_100g":   nutrientes["proteinas_g"],
        "carbohidratos_100g": nutrientes["carbohidratos_g"],
        "grasas_100g":      nutrientes["grasas_g"],
        "fibra_100g":       nutrientes["fibra_g"],
    }


async def _search_usda(q: str, limit: int) -> List[dict]:
    params = {"query": q, "api_key": USDA_KEY, "dataType": "Foundation,SR Legacy", "pageSize": limit}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(USDA_URL, params=params)
            res.raise_for_status()
            data = res.json()
    except Exception:
        return []
    return [_parse_food(f) for f in data.get("foods", [])]


@router.get("/search")
async def search_alimentos(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
) -> List[dict]:
    """Busca primero en la base local (sin distinguir tildes ni mayúsculas, todas
    las palabras deben aparecer) y completa con USDA si hay pocos resultados."""
    words = [w for w in normalize(q).split() if w]
    query = db.query(models.Alimento)
    for w in words:
        query = query.filter(models.Alimento.nombre_norm.like(f"%{w}%"))
    local = query.all()
    first = words[0] if words else ""
    # Primero los que empiezan con la búsqueda y los chilenos; luego por nombre corto
    local.sort(key=lambda a: (not normalize(a.nombre).startswith(first), a.fuente != "chile", len(a.nombre)))
    results = [_local_to_dict(a) for a in local[:MAX_RESULTS]]
    if len(results) < 5:
        results += await _search_usda(q, MAX_RESULTS - len(results))
    return results
