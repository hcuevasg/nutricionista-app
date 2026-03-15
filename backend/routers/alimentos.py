"""Búsqueda de alimentos via USDA FoodData Central."""
import os
import httpx
from fastapi import APIRouter, Depends, Query
from typing import List
import models
import auth

router = APIRouter(prefix="/alimentos", tags=["alimentos"])

USDA_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
USDA_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Nutrient IDs en FoodData Central
_NID = {
    1008: "calorias",        # Energy (kcal)
    1003: "proteinas_g",     # Protein
    1005: "carbohidratos_g", # Carbohydrate, by difference
    1004: "grasas_g",        # Total lipid (fat)
    1079: "fibra_g",         # Fiber, total dietary
}


def _parse_food(food: dict) -> dict | None:
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
        "calorias_100g":    nutrientes["calorias"],
        "proteinas_100g":   nutrientes["proteinas_g"],
        "carbohidratos_100g": nutrientes["carbohidratos_g"],
        "grasas_100g":      nutrientes["grasas_g"],
        "fibra_100g":       nutrientes["fibra_g"],
    }


@router.get("/search")
async def search_alimentos(
    q: str = Query(..., min_length=2),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
) -> List[dict]:
    """Busca alimentos en USDA FoodData Central y devuelve macros por 100g."""
    params = {
        "query":    q,
        "api_key":  USDA_KEY,
        "dataType": "Foundation,SR Legacy",
        "pageSize": 15,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(USDA_URL, params=params)
            res.raise_for_status()
            data = res.json()
    except Exception:
        return []

    results = []
    for food in data.get("foods", []):
        parsed = _parse_food(food)
        if parsed:
            results.append(parsed)
    return results
