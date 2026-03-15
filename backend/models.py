"""SQLAlchemy models for database."""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patients = relationship("Patient", back_populates="nutritionist", cascade="all, delete-orphan")


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
