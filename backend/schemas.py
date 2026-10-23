"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List, Generic, Literal, TypeVar
from datetime import datetime

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int


# ── Auth Schemas ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    email: EmailStr
    password: str = Field(max_length=128)
    invite_code: Optional[str] = Field(None, max_length=128)


class LoginResponse(BaseModel):
    # Con verificación en dos pasos activa, el login entrega requires_2fa y un
    # challenge_token (5 min) en vez de access_token.
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[dict] = None
    requires_2fa: bool = False
    challenge_token: Optional[str] = None


class TwoFactorVerifyRequest(BaseModel):
    challenge_token: str
    code: str


class TwoFactorCodeRequest(BaseModel):
    code: str


class TwoFactorDisableRequest(BaseModel):
    password: str
    code: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    name: Optional[str] = None
    clinic_name: Optional[str] = None
    report_tagline: Optional[str] = None
    logo_base64: Optional[str] = None
    totp_enabled: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    clinic_name: Optional[str] = None
    report_tagline: Optional[str] = None
    logo_base64: Optional[str] = Field(None, max_length=800_000)  # "" quita el logo

    @field_validator('logo_base64')
    @classmethod
    def valid_logo(cls, v):
        if not v:
            return v
        import image_utils
        return image_utils.clean_logo(v)


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)


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
    consent_at: Optional[datetime] = None
    consent_version: Optional[str] = None
    consent_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

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


class NotaEvolucionCreate(BaseModel):
    fecha: str
    motivo: Optional[str] = None
    subjetivo: Optional[str] = None
    objetivo: Optional[str] = None
    analisis: Optional[str] = None
    plan: Optional[str] = None
    proximo_control: Optional[str] = None

    @field_validator('fecha', 'proximo_control')
    @classmethod
    def iso_date(cls, v):
        if v in (None, ''):
            return None
        datetime.strptime(v[:10], '%Y-%m-%d')
        return v[:10]


class NotaEvolucionResponse(NotaEvolucionCreate):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamenResultado(BaseModel):
    analito: str
    valor: float
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    notas: Optional[str] = None


class ExamenesCreate(BaseModel):
    fecha: str
    resultados: List[ExamenResultado]

    @field_validator('fecha')
    @classmethod
    def iso_date(cls, v):
        datetime.strptime(v[:10], '%Y-%m-%d')
        return v[:10]


class ExamenResponse(BaseModel):
    id: int
    fecha: str
    analito: str
    nombre: str
    grupo: str
    valor: float
    unidad: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    estado: str
    notas: Optional[str] = None


class PatientConsentRequest(BaseModel):
    accepted: bool


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
    tibiale_height_cm: Optional[float] = None
    arm_span_cm: Optional[float] = None

    # Calculados (computed in frontend, stored for history)
    body_density: Optional[float] = None
    fat_mass_pct: Optional[float] = None
    fat_mass_kg: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    sum_6_skinfolds: Optional[float] = None
    somatotype_endo: Optional[float] = None
    somatotype_meso: Optional[float] = None
    somatotype_ecto: Optional[float] = None

    # Metas para la próxima evaluación
    goals_text: Optional[str] = None
    next_eval_date: Optional[str] = None


class AnthropometricResponse(AnthropometricCreate):
    id: int
    patient_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Plantillas de pauta ───────────────────────────────────────────
class PlantillaPautaCreate(BaseModel):
    nombre: str
    tipo_pauta: str
    fa_key: str
    ajuste_kcal: Optional[float] = None
    prot_pct: float
    lip_pct: float
    porciones_json: str
    distribucion_json: str
    menu_json: Optional[str] = None
    notes: Optional[str] = None


class PlantillaPautaResponse(PlantillaPautaCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Pautas ────────────────────────────────────────────────────────
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
    is_active: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Antecedentes Schemas ───────────────────────────────────────────
class AntecedentesBase(BaseModel):
    identidad_genero: Optional[str] = None
    estado_civil: Optional[str] = None
    prevision: Optional[str] = None
    horario_trabajo: Optional[str] = None
    tipo_traslado: Optional[str] = None
    nutricionista_previo: Optional[bool] = None
    observacion_nutricionista_previo: Optional[str] = None
    motivo_consulta: Optional[str] = None
    tipo_alimentacion: Optional[str] = None
    peso_habitual: Optional[float] = None
    peso_maximo: Optional[float] = None
    peso_minimo: Optional[float] = None
    peso_oscilaciones: Optional[str] = None
    enfermedades_preexistentes: Optional[str] = None
    antecedentes_familiares: Optional[str] = None
    farmacos_suplementos: Optional[str] = None
    suplementacion_b12: Optional[str] = None
    cirugias: Optional[str] = None
    dietas_moda: Optional[str] = None
    tabaco_alcohol: Optional[str] = None
    ejercicio_frecuencia: Optional[str] = None
    ejercicio_duracion: Optional[str] = None
    ejercicio_intensidad: Optional[str] = None
    ejercicio_objetivo: Optional[str] = None
    observacion_actividad_fisica: Optional[str] = None
    con_quien_vive: Optional[str] = None
    mascotas: Optional[str] = None
    relacion_familiar: Optional[str] = None
    quien_cocina: Optional[str] = None
    gusta_cocinar: Optional[bool] = None
    sale_fines_semana: Optional[bool] = None
    transito_intestinal: Optional[str] = None
    sintomas_gi: Optional[str] = None
    evento_traumatico: Optional[str] = None
    intolerancias: Optional[str] = None
    aversiones: Optional[str] = None
    alimentos_gustados: Optional[str] = None
    comida_emocional: Optional[str] = None
    tiempo_comidas: Optional[str] = None
    come_distracciones: Optional[bool] = None
    calificacion_alimentacion: Optional[int] = None
    recordatorio_semana: Optional[str] = None
    recordatorio_finde: Optional[str] = None
    metas_corto_plazo: Optional[str] = None
    metas_largo_plazo: Optional[str] = None
    signos_carenciales: Optional[str] = None


class AntecedentesCreate(AntecedentesBase):
    pass


class AntecedentesResponse(AntecedentesBase):
    id: int
    patient_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Receta Schemas ─────────────────────────────────────────────────
class RecetaIngredienteCreate(BaseModel):
    nombre_alimento: str
    gramos: float = 100
    medida_casera: Optional[str] = None
    calorias: float = 0
    proteinas_g: float = 0
    carbohidratos_g: float = 0
    grasas_g: float = 0
    fibra_g: float = 0


class RecetaIngredienteResponse(RecetaIngredienteCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RecetaEquivalenciaItem(BaseModel):
    grupo: str
    porciones: float


class RecetaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    categoria: str = "General"
    porciones_rinde: int = 1
    notas: Optional[str] = None


class RecetaUpdate(RecetaCreate):
    ingredientes: Optional[List[RecetaIngredienteCreate]] = None
    equivalencias: Optional[List[RecetaEquivalenciaItem]] = None


class RecetaResponse(RecetaCreate):
    id: int
    nutritionist_id: int
    created_at: datetime
    ingredientes: List[RecetaIngredienteResponse] = []
    equivalencias: List[RecetaEquivalenciaItem] = []

    model_config = ConfigDict(from_attributes=True)


class RecetaListItem(RecetaCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Appointment Schemas ────────────────────────────────────────────
AppointmentStatus = Literal["scheduled", "completed", "cancelled"]


class AppointmentCreate(BaseModel):
    patient_id: Optional[int] = None
    scheduled_at: datetime
    duration_minutes: int = Field(45, ge=5, le=480)
    notes: Optional[str] = None
    status: AppointmentStatus = "scheduled"

class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None

class AppointmentResponse(BaseModel):
    id: int
    nutritionist_id: int
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    notes: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Portal Schemas ─────────────────────────────────────────────────
class ShareTokenCreate(BaseModel):
    patient_id: int
    days_valid: int = 30

class ShareTokenResponse(BaseModel):
    id: int
    token: str
    patient_id: int
    patient_name: str
    expires_at: datetime
    revoked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PortalInfo(BaseModel):
    patient_name: str
    nutritionist_name: Optional[str] = None
    clinic_name: Optional[str] = None
    consent_at: Optional[datetime] = None
    consent_version: Optional[str] = None
    current_consent_version: str

class PortalPauta(BaseModel):
    """Lo que ve el paciente de su pauta: sin cálculos internos ni notas del profesional."""
    id: int
    name: str
    date: str
    tipo_pauta: Optional[str] = None
    kcal_objetivo: Optional[float] = None
    prot_pct: Optional[float] = None
    lip_pct: Optional[float] = None
    cho_pct: Optional[float] = None
    menu_json: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PortalEvaluationSummary(BaseModel):
    id: int
    date: str
    weight_kg: Optional[float] = None
    fat_mass_pct: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    sum_6_skinfolds: Optional[float] = None
    waist_cm: Optional[float] = None
    goals_text: Optional[str] = None
    next_eval_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Largos máximos ────────────────────────────────────────────────
# Cada texto que entra al API respeta el largo de su columna en la base
# (String(n)): un valor más largo se rechaza con 422 en vez de fallar en Postgres.
def _limit_to_columns() -> None:
    import annotated_types
    import models
    pairs = [
        (PatientCreate, models.Patient), (ProfileUpdate, models.Nutritionist),
        (AnthropometricCreate, models.Anthropometric), (PautaCreate, models.Pauta),
        (AntecedentesCreate, models.Antecedentes), (AppointmentCreate, models.Appointment),
        (AppointmentUpdate, models.Appointment), (NotaEvolucionCreate, models.NotaEvolucion),
        (ExamenResultado, models.ExamenLaboratorio), (PlantillaPautaCreate, models.PlantillaPauta),
        (RecetaCreate, models.Receta), (RecetaUpdate, models.Receta),
        (RecetaIngredienteCreate, models.RecetaIngrediente),
    ]
    for schema, model in pairs:
        columns = model.__table__.columns
        changed = False
        for name, field in schema.model_fields.items():
            col = columns.get(name)
            # EncryptedText guarda más caracteres que el texto en claro: vale max_chars
            length = getattr(getattr(col, "type", None), "max_chars", None) or \
                getattr(getattr(col, "type", None), "length", None)
            if length and not any(isinstance(m, annotated_types.MaxLen) for m in field.metadata):
                field.metadata.append(annotated_types.MaxLen(length))
                changed = True
        if changed:
            schema.model_rebuild(force=True)


_limit_to_columns()
