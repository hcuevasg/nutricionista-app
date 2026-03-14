"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Auth Schemas ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Patient Schemas ───────────────────────────────────────────────
class PatientCreate(BaseModel):
    name: str
    birth_date: Optional[str] = None
    sex: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    notes: Optional[str] = None


class PatientUpdate(PatientCreate):
    pass


class PatientResponse(PatientCreate):
    id: int
    nutritionist_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Anthropometric Schemas ────────────────────────────────────────
class AnthropometricCreate(BaseModel):
    date: str
    session_date: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    triceps_mm: Optional[float] = None
    subscapular_mm: Optional[float] = None
    biceps_mm: Optional[float] = None
    iliac_crest_mm: Optional[float] = None
    supraspinal_mm: Optional[float] = None
    abdominal_mm: Optional[float] = None
    medial_thigh_mm: Optional[float] = None
    max_calf_mm: Optional[float] = None
    isak_level: str = "ISAK 1"


class AnthropometricResponse(AnthropometricCreate):
    id: int
    patient_id: int
    body_density: Optional[float] = None
    fat_mass_pct: Optional[float] = None
    fat_mass_kg: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Meal Plan Schemas ─────────────────────────────────────────────
class MealItemCreate(BaseModel):
    meal_type: str
    food_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class MealItemResponse(MealItemCreate):
    id: int
    plan_id: int

    class Config:
        from_attributes = True


class MealPlanCreate(BaseModel):
    name: str
    date: str
    goal: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    notes: Optional[str] = None
    items: List[MealItemCreate] = []


class MealPlanResponse(BaseModel):
    id: int
    patient_id: int
    name: str
    date: str
    goal: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    notes: Optional[str] = None
    items: List[MealItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
