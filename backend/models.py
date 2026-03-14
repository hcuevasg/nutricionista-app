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
    sex = Column(String(1))  # M/F
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    occupation = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    nutritionist = relationship("Nutritionist", back_populates="patients")
    anthropometrics = relationship("Anthropometric", back_populates="patient", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="patient", cascade="all, delete-orphan")


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

    # Pliegues cutáneos (mm) - ISAK 1
    triceps_mm = Column(Float, nullable=True)
    subscapular_mm = Column(Float, nullable=True)
    biceps_mm = Column(Float, nullable=True)
    iliac_crest_mm = Column(Float, nullable=True)
    supraspinal_mm = Column(Float, nullable=True)
    abdominal_mm = Column(Float, nullable=True)
    medial_thigh_mm = Column(Float, nullable=True)
    max_calf_mm = Column(Float, nullable=True)

    # Calculados
    body_density = Column(Float, nullable=True)
    fat_mass_pct = Column(Float, nullable=True)
    fat_mass_kg = Column(Float, nullable=True)
    lean_mass_kg = Column(Float, nullable=True)

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
