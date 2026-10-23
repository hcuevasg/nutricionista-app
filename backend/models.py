"""SQLAlchemy models for database."""
from crypto_fields import EncryptedText
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Index, func, false as sa_false
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from timeutil import utcnow


class Nutritionist(Base):
    """Nutricionista/Usuario."""
    __tablename__ = "nutritionists"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    name = Column(String(255), nullable=True)
    clinic_name = Column(String(255), nullable=True)
    report_tagline = Column(String(500), nullable=True)
    logo_base64 = Column(Text, nullable=True)
    # Verificación en dos pasos (TOTP). El secreto se guarda al iniciar la
    # configuración y solo se exige cuando totp_enabled es True.
    totp_secret = Column(EncryptedText(64), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False, server_default=sa_false())
    totp_recovery_codes = Column(Text, nullable=True)   # JSON con hashes bcrypt
    totp_last_step = Column(Integer, nullable=True)  # paso TOTP del último código aceptado (anti-reuso)
    # Seguridad de la cuenta: bloqueo por intentos fallidos y versión de sesión (invalida tokens)
    failed_logins = Column(Integer, default=0, nullable=False, server_default="0")
    locked_until = Column(DateTime, nullable=True)
    token_version = Column(Integer, default=0, nullable=False, server_default="0")
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    patients = relationship("Patient", back_populates="nutritionist", cascade="all, delete-orphan")
    recetas = relationship("Receta", back_populates="nutritionist", cascade="all, delete-orphan")


class Patient(Base):
    """Paciente."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id"), index=True)
    name = Column(String(255))
    birth_date = Column(String)
    age = Column(Integer, nullable=True)
    sex = Column(String(20))  # M/F or Masculino/Femenino
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(EncryptedText(255), nullable=True)
    occupation = Column(EncryptedText(255), nullable=True)
    notes = Column(EncryptedText(), nullable=True)
    allergies = Column(EncryptedText(), nullable=True)  # JSON array: ["gluten", "lacteos", ...]
    # Consentimiento informado para tratar datos de salud (Ley 19.628 / 21.719)
    consent_at = Column(DateTime, nullable=True)
    consent_version = Column(String(20), nullable=True)
    consent_source = Column(String(20), nullable=True)   # profesional | portal
    consent_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    nutritionist = relationship("Nutritionist", back_populates="patients")
    anthropometrics = relationship("Anthropometric", back_populates="patient", cascade="all, delete-orphan")
    pautas = relationship("Pauta", back_populates="patient", cascade="all, delete-orphan")
    notas_evolucion = relationship("NotaEvolucion", cascade="all, delete-orphan")
    examenes_laboratorio = relationship("ExamenLaboratorio", cascade="all, delete-orphan")
    antecedentes = relationship("Antecedentes", back_populates="patient", uselist=False)


class Anthropometric(Base):
    """Evaluación ISAK."""
    __tablename__ = "anthropometrics"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    date = Column(String)
    session_date = Column(String, nullable=True)

    # Datos básicos
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)

    # Perímetros (cm) — ISAK 1+2
    arm_relaxed_cm = Column(Float, nullable=True)
    arm_contracted_cm = Column(Float, nullable=True)
    hip_glute_cm = Column(Float, nullable=True)
    thigh_max_cm = Column(Float, nullable=True)
    thigh_mid_cm = Column(Float, nullable=True)
    calf_cm = Column(Float, nullable=True)

    # Pliegues cutáneos (mm) — ISAK 1+2
    triceps_mm = Column(Float, nullable=True)
    subscapular_mm = Column(Float, nullable=True)
    biceps_mm = Column(Float, nullable=True)
    iliac_crest_mm = Column(Float, nullable=True)
    supraspinal_mm = Column(Float, nullable=True)
    abdominal_mm = Column(Float, nullable=True)
    medial_thigh_mm = Column(Float, nullable=True)
    max_calf_mm = Column(Float, nullable=True)

    # Pliegues adicionales (mm) — ISAK 2
    pectoral_mm = Column(Float, nullable=True)
    axillary_mm = Column(Float, nullable=True)
    front_thigh_mm = Column(Float, nullable=True)

    # Perímetros adicionales (cm) — ISAK 2
    head_cm = Column(Float, nullable=True)
    neck_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    ankle_min_cm = Column(Float, nullable=True)

    # Diámetros óseos (cm) — ISAK 2
    humerus_width_cm = Column(Float, nullable=True)
    femur_width_cm = Column(Float, nullable=True)
    biacromial_cm = Column(Float, nullable=True)
    biiliocrestal_cm = Column(Float, nullable=True)
    ap_chest_cm = Column(Float, nullable=True)
    transv_chest_cm = Column(Float, nullable=True)
    foot_length_cm = Column(Float, nullable=True)
    wrist_cm = Column(Float, nullable=True)
    ankle_bimalleolar_cm = Column(Float, nullable=True)

    # Longitudes (cm) — ISAK 2
    acromion_radial_cm = Column(Float, nullable=True)
    radial_styloid_cm = Column(Float, nullable=True)
    iliospinal_height_cm = Column(Float, nullable=True)
    trochanter_tibial_cm = Column(Float, nullable=True)
    tibiale_height_cm = Column(Float, nullable=True)
    arm_span_cm = Column(Float, nullable=True)

    # Calculados
    body_density = Column(Float, nullable=True)
    fat_mass_pct = Column(Float, nullable=True)
    fat_mass_kg = Column(Float, nullable=True)
    lean_mass_kg = Column(Float, nullable=True)
    sum_6_skinfolds = Column(Float, nullable=True)
    somatotype_endo = Column(Float, nullable=True)
    somatotype_meso = Column(Float, nullable=True)
    somatotype_ecto = Column(Float, nullable=True)

    # ISAK Level
    isak_level = Column(String(20), default="ISAK 1")

    # Metas para la próxima evaluación (una por línea) y fecha estimada
    goals_text = Column(EncryptedText(), nullable=True)
    next_eval_date = Column(String, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    # Relationship
    patient = relationship("Patient", back_populates="anthropometrics")


class PlantillaPauta(Base):
    """Plantilla reutilizable de pauta (sin datos del paciente)."""
    __tablename__ = "plantillas_pauta"

    id = Column(Integer, primary_key=True, index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id", ondelete="CASCADE"), index=True)
    nombre = Column(String(255), nullable=False)
    tipo_pauta = Column(String(50))
    fa_key = Column(String(50))
    ajuste_kcal = Column(Float, nullable=True)
    prot_pct = Column(Float)
    lip_pct = Column(Float)
    porciones_json = Column(Text)
    distribucion_json = Column(Text)
    menu_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class Pauta(Base):
    """Pauta de alimentación."""
    __tablename__ = "pautas"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    name = Column(String(255))
    date = Column(String)
    tipo_pauta = Column(String(50))         # omnivoro, ovolacto, vegano, etc.
    sexo = Column(String(20))
    edad = Column(Integer)
    peso = Column(Float)
    fa_key = Column(String(50))             # sedentaria, liviana, moderada, intensa
    tmb = Column(Float)
    get_kcal = Column(Float)
    kcal_objetivo = Column(Float)
    ajuste_kcal = Column(Float, nullable=True)
    prot_g_kg = Column(Float)
    prot_g = Column(Float)
    prot_kcal = Column(Float)
    prot_pct = Column(Float)
    lip_pct = Column(Float)
    lip_g = Column(Float)
    lip_kcal = Column(Float)
    cho_g = Column(Float)
    cho_kcal = Column(Float)
    cho_pct = Column(Float)
    porciones_json = Column(Text)           # JSON: {grupo: porciones}
    distribucion_json = Column(Text)        # JSON: {tiempo: {grupo: porciones}}
    menu_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False) # JSON: {tiempo: {opcion1: str, opcion2: str}}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="pautas")


class ErrorLog(Base):
    """Error no controlado del backend o reportado por el frontend (registro interno)."""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id", ondelete="CASCADE"), nullable=True, index=True)
    source = Column(String(20))        # backend | frontend
    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=True)
    error_type = Column(String(120), nullable=True)
    message = Column(Text, nullable=True)
    stack = Column(Text, nullable=True)
    user_agent = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)


class AuditLog(Base):
    """Registro de auditoría de acciones."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id"), nullable=True, index=True)
    action = Column(String(50))        # login, logout, create, update, delete, export
    resource = Column(String(50))      # patient, anthropometric, pauta, meal_plan, pdf
    resource_id = Column(Integer, nullable=True)
    detail = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    nutritionist = relationship("Nutritionist")


class ExamenLaboratorio(Base):
    """Resultado de un examen de laboratorio (un analito en una fecha)."""
    __tablename__ = "examenes_laboratorio"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = Column(String(10), nullable=False)
    analito = Column(String(50), nullable=False)   # clave de lab_catalog.CATALOG
    valor = Column(Float, nullable=False)
    unidad = Column(String(20), nullable=True)
    ref_min = Column(Float, nullable=True)         # rango usado al registrar (el del laboratorio)
    ref_max = Column(Float, nullable=True)
    notas = Column(EncryptedText(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)


class NotaEvolucion(Base):
    """Nota de evolución de una consulta (formato SOAP)."""
    __tablename__ = "notas_evolucion"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = Column(String(10), nullable=False)  # YYYY-MM-DD, como el resto de las fechas
    motivo = Column(EncryptedText(255), nullable=True)
    subjetivo = Column(EncryptedText(), nullable=True)     # S: lo que relata el paciente
    objetivo = Column(EncryptedText(), nullable=True)      # O: mediciones y hallazgos
    analisis = Column(EncryptedText(), nullable=True)      # A: evaluación/diagnóstico nutricional
    plan = Column(EncryptedText(), nullable=True)          # P: indicaciones y acuerdos
    proximo_control = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Antecedentes(Base):
    """Antecedentes clínicos del paciente."""
    __tablename__ = "antecedentes"
    # Índice creado por la migración heredada (main.py); declarado para que
    # `alembic revision --autogenerate` no proponga borrarlo.
    __table_args__ = (Index("ix_antecedentes_patient_id", "patient_id"),)

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Tab 1 - Identificación
    identidad_genero = Column(EncryptedText(), nullable=True)
    estado_civil = Column(EncryptedText(), nullable=True)
    prevision = Column(EncryptedText(), nullable=True)
    horario_trabajo = Column(EncryptedText(), nullable=True)
    tipo_traslado = Column(EncryptedText(), nullable=True)
    nutricionista_previo = Column(Boolean, nullable=True)
    observacion_nutricionista_previo = Column(EncryptedText(), nullable=True)
    motivo_consulta = Column(EncryptedText(), nullable=True)
    tipo_alimentacion = Column(EncryptedText(), nullable=True)

    # Tab 2 - Historial peso
    peso_habitual = Column(Float, nullable=True)
    peso_maximo = Column(Float, nullable=True)
    peso_minimo = Column(Float, nullable=True)
    peso_oscilaciones = Column(EncryptedText(), nullable=True)

    # Tab 3 - Anamnesis remota
    enfermedades_preexistentes = Column(EncryptedText(), nullable=True)
    antecedentes_familiares = Column(EncryptedText(), nullable=True)
    farmacos_suplementos = Column(EncryptedText(), nullable=True)
    suplementacion_b12 = Column(EncryptedText(), nullable=True)
    cirugias = Column(EncryptedText(), nullable=True)
    dietas_moda = Column(EncryptedText(), nullable=True)
    tabaco_alcohol = Column(EncryptedText(), nullable=True)
    ejercicio_frecuencia = Column(EncryptedText(), nullable=True)
    ejercicio_duracion = Column(EncryptedText(), nullable=True)
    ejercicio_intensidad = Column(EncryptedText(), nullable=True)
    ejercicio_objetivo = Column(EncryptedText(), nullable=True)
    observacion_actividad_fisica = Column(EncryptedText(), nullable=True)

    # Tab 4 - Antecedentes sociales
    con_quien_vive = Column(EncryptedText(), nullable=True)
    mascotas = Column(EncryptedText(), nullable=True)
    relacion_familiar = Column(EncryptedText(), nullable=True)
    quien_cocina = Column(EncryptedText(), nullable=True)
    gusta_cocinar = Column(Boolean, nullable=True)
    sale_fines_semana = Column(Boolean, nullable=True)

    # Tab 5 - Anamnesis alimentaria
    transito_intestinal = Column(EncryptedText(), nullable=True)
    sintomas_gi = Column(EncryptedText(), nullable=True)
    evento_traumatico = Column(EncryptedText(), nullable=True)
    intolerancias = Column(EncryptedText(), nullable=True)
    aversiones = Column(EncryptedText(), nullable=True)
    alimentos_gustados = Column(EncryptedText(), nullable=True)
    comida_emocional = Column(EncryptedText(), nullable=True)
    tiempo_comidas = Column(EncryptedText(), nullable=True)
    come_distracciones = Column(Boolean, nullable=True)
    calificacion_alimentacion = Column(Integer, nullable=True)

    # Tab 6 - Recordatorio 24hrs (JSON stored as Text)
    recordatorio_semana = Column(EncryptedText(), nullable=True)  # JSON string
    recordatorio_finde = Column(EncryptedText(), nullable=True)   # JSON string

    # Tab 7 - Metas + signos
    metas_corto_plazo = Column(EncryptedText(), nullable=True)
    metas_largo_plazo = Column(EncryptedText(), nullable=True)
    signos_carenciales = Column(EncryptedText(), nullable=True)   # JSON string

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="antecedentes")


class Alimento(Base):
    """Catálogo global de alimentos (valores por 100 g), compartido por todos."""
    __tablename__ = "alimentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    nombre_en = Column(String(255), nullable=True)
    nombre_norm = Column(String(255), index=True)   # minúsculas y sin tildes, para buscar
    calorias_100g = Column(Float, default=0)
    proteinas_100g = Column(Float, default=0)
    carbohidratos_100g = Column(Float, default=0)
    grasas_100g = Column(Float, default=0)
    fibra_100g = Column(Float, default=0)
    fuente = Column(String(30), default="base")     # base | chile


class Receta(Base):
    """Receta personalizada del nutricionista."""
    __tablename__ = "recetas"

    id = Column(Integer, primary_key=True, index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id"), index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String(100), default="General")
    porciones_rinde = Column(Integer, default=1)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    nutritionist = relationship("Nutritionist", back_populates="recetas")
    ingredientes = relationship("RecetaIngrediente", back_populates="receta", cascade="all, delete-orphan")
    equivalencias = relationship("RecetaEquivalencia", back_populates="receta", cascade="all, delete-orphan")


class RecetaIngrediente(Base):
    """Ingrediente de una receta con sus macros."""
    __tablename__ = "receta_ingredientes"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("recetas.id"), index=True)
    nombre_alimento = Column(String(255), nullable=False)
    gramos = Column(Float, default=100)
    medida_casera = Column(String(100), nullable=True)
    calorias = Column(Float, default=0)
    proteinas_g = Column(Float, default=0)
    carbohidratos_g = Column(Float, default=0)
    grasas_g = Column(Float, default=0)
    fibra_g = Column(Float, default=0)

    receta = relationship("Receta", back_populates="ingredientes")


class RecetaEquivalencia(Base):
    """Equivalencia de 1 porción de receta en grupos alimentarios."""
    __tablename__ = "receta_equivalencias"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("recetas.id"), index=True)
    grupo = Column(String(100), nullable=False)
    porciones = Column(Float, default=0)

    receta = relationship("Receta", back_populates="equivalencias")


class PatientShareToken(Base):
    """Token de acceso al portal del paciente."""
    __tablename__ = "patient_share_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id"), index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    revoked = Column(Boolean, default=False)
    patient = relationship("Patient")
    nutritionist = relationship("Nutritionist")


class Appointment(Base):
    """Cita / consulta agendada."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    nutritionist_id = Column(Integer, ForeignKey("nutritionists.id", ondelete="CASCADE"), index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=45)
    notes = Column(EncryptedText(), nullable=True)
    status = Column(String(20), default="scheduled")  # scheduled/completed/cancelled
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    nutritionist = relationship("Nutritionist")
    patient = relationship("Patient")
