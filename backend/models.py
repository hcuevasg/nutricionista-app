"""SQLAlchemy models for database."""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    address = Column(String(255), nullable=True)
    occupation = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)  # JSON array: ["gluten", "lacteos", ...]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    nutritionist = relationship("Nutritionist", back_populates="patients")
    anthropometrics = relationship("Anthropometric", back_populates="patient", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="patient", cascade="all, delete-orphan")
    pautas = relationship("Pauta", back_populates="patient", cascade="all, delete-orphan")
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

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("Patient", back_populates="anthropometrics")


class MealPlan(Base):
    """Plan alimenticio."""
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    name = Column(String(255))
    date = Column(String)
    goal = Column(String(255), nullable=True)
    calories = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="meal_plans")
    items = relationship("MealItem", back_populates="meal_plan", cascade="all, delete-orphan")


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
    menu_json = Column(Text, nullable=True) # JSON: {tiempo: {opcion1: str, opcion2: str}}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="pautas")


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
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    nutritionist = relationship("Nutritionist")


class Antecedentes(Base):
    """Antecedentes clínicos del paciente."""
    __tablename__ = "antecedentes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Tab 1 - Identificación
    identidad_genero = Column(String, nullable=True)
    estado_civil = Column(String, nullable=True)
    prevision = Column(String, nullable=True)
    horario_trabajo = Column(String, nullable=True)
    tipo_traslado = Column(String, nullable=True)
    nutricionista_previo = Column(Boolean, nullable=True)
    observacion_nutricionista_previo = Column(Text, nullable=True)
    motivo_consulta = Column(Text, nullable=True)
    tipo_alimentacion = Column(String, nullable=True)

    # Tab 2 - Historial peso
    peso_habitual = Column(Float, nullable=True)
    peso_maximo = Column(Float, nullable=True)
    peso_minimo = Column(Float, nullable=True)
    peso_oscilaciones = Column(Text, nullable=True)

    # Tab 3 - Anamnesis remota
    enfermedades_preexistentes = Column(Text, nullable=True)
    antecedentes_familiares = Column(Text, nullable=True)
    farmacos_suplementos = Column(Text, nullable=True)
    suplementacion_b12 = Column(Text, nullable=True)
    cirugias = Column(Text, nullable=True)
    dietas_moda = Column(Text, nullable=True)
    tabaco_alcohol = Column(Text, nullable=True)
    ejercicio_frecuencia = Column(String, nullable=True)
    ejercicio_duracion = Column(String, nullable=True)
    ejercicio_intensidad = Column(String, nullable=True)
    ejercicio_objetivo = Column(Text, nullable=True)
    observacion_actividad_fisica = Column(Text, nullable=True)

    # Tab 4 - Antecedentes sociales
    con_quien_vive = Column(String, nullable=True)
    mascotas = Column(String, nullable=True)
    relacion_familiar = Column(Text, nullable=True)
    quien_cocina = Column(String, nullable=True)
    gusta_cocinar = Column(Boolean, nullable=True)
    sale_fines_semana = Column(Boolean, nullable=True)

    # Tab 5 - Anamnesis alimentaria
    transito_intestinal = Column(Text, nullable=True)
    sintomas_gi = Column(Text, nullable=True)
    evento_traumatico = Column(Text, nullable=True)
    intolerancias = Column(Text, nullable=True)
    aversiones = Column(Text, nullable=True)
    alimentos_gustados = Column(Text, nullable=True)
    comida_emocional = Column(Text, nullable=True)
    tiempo_comidas = Column(String, nullable=True)
    come_distracciones = Column(Boolean, nullable=True)
    calificacion_alimentacion = Column(Integer, nullable=True)

    # Tab 6 - Recordatorio 24hrs (JSON stored as Text)
    recordatorio_semana = Column(Text, nullable=True)  # JSON string
    recordatorio_finde = Column(Text, nullable=True)   # JSON string

    # Tab 7 - Metas + signos
    metas_corto_plazo = Column(Text, nullable=True)
    metas_largo_plazo = Column(Text, nullable=True)
    signos_carenciales = Column(Text, nullable=True)   # JSON string

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="antecedentes")


class MealItem(Base):
    """Item en plan alimenticio."""
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("meal_plans.id"), index=True)
    meal_type = Column(String(50))  # desayuno, almuerzo, etc.
    food_name = Column(String(255))
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    calories = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)

    # Relationship
    meal_plan = relationship("MealPlan", back_populates="items")


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)
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
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="scheduled")  # scheduled/completed/cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    nutritionist = relationship("Nutritionist")
    patient = relationship("Patient")
