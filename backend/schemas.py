"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, field_validator
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


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


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
    allergies: Optional[List[str]] = []


class PatientUpdate(PatientCreate):
    pass


class PatientResponse(PatientCreate):
    id: int
    nutritionist_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('allergies', mode='before')
    @classmethod
    def parse_allergies(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []


# ── Anthropometric Schemas ────────────────────────────────────────
class AnthropometricCreate(BaseModel):
    date: str
    session_date: Optional[str] = None
    isak_level: str = "ISAK 1"

    # Datos básicos
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    waist_cm: Optional[float] = None

    # Perímetros (cm) — ISAK 1+2
    arm_relaxed_cm: Optional[float] = None
    arm_contracted_cm: Optional[float] = None
    hip_glute_cm: Optional[float] = None
    thigh_max_cm: Optional[float] = None
    thigh_mid_cm: Optional[float] = None
    calf_cm: Optional[float] = None

    # Pliegues cutáneos (mm) — ISAK 1+2
    triceps_mm: Optional[float] = None
    subscapular_mm: Optional[float] = None
    biceps_mm: Optional[float] = None
    iliac_crest_mm: Optional[float] = None
    supraspinal_mm: Optional[float] = None
    abdominal_mm: Optional[float] = None
    medial_thigh_mm: Optional[float] = None
    max_calf_mm: Optional[float] = None

    # Pliegues adicionales (mm) — ISAK 2
    pectoral_mm: Optional[float] = None
    axillary_mm: Optional[float] = None
    front_thigh_mm: Optional[float] = None

    # Perímetros adicionales (cm) — ISAK 2
    head_cm: Optional[float] = None
    neck_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    ankle_min_cm: Optional[float] = None

    # Diámetros óseos (cm) — ISAK 2
    humerus_width_cm: Optional[float] = None
    femur_width_cm: Optional[float] = None
    biacromial_cm: Optional[float] = None
    biiliocrestal_cm: Optional[float] = None
    ap_chest_cm: Optional[float] = None
    transv_chest_cm: Optional[float] = None
    foot_length_cm: Optional[float] = None
    wrist_cm: Optional[float] = None
    ankle_bimalleolar_cm: Optional[float] = None

    # Longitudes (cm) — ISAK 2
    acromion_radial_cm: Optional[float] = None
    radial_styloid_cm: Optional[float] = None
    iliospinal_height_cm: Optional[float] = None
    trochanter_tibial_cm: Optional[float] = None

    # Calculados (computed in frontend, stored for history)
    body_density: Optional[float] = None
    fat_mass_pct: Optional[float] = None
    fat_mass_kg: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    sum_6_skinfolds: Optional[float] = None
    somatotype_endo: Optional[float] = None
    somatotype_meso: Optional[float] = None
    somatotype_ecto: Optional[float] = None


class AnthropometricResponse(AnthropometricCreate):
    id: int
    patient_id: int
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


# ── Pauta Schemas ──────────────────────────────────────────────────
class PautaCreate(BaseModel):
    name: str
    date: str
    tipo_pauta: str
    sexo: str
    edad: int
    peso: float
    fa_key: str
    tmb: float
    get_kcal: float
    kcal_objetivo: float
    ajuste_kcal: Optional[float] = None
    prot_g_kg: float
    prot_g: float
    prot_kcal: float
    prot_pct: float
    lip_pct: float
    lip_g: float
    lip_kcal: float
    cho_g: float
    cho_kcal: float
    cho_pct: float
    porciones_json: str
    distribucion_json: str
    menu_json: Optional[str] = None
    notes: Optional[str] = None


class PautaResponse(PautaCreate):
    id: int
    patient_id: int
    created_at: datetime

    class Config:
        from_attributes = True
