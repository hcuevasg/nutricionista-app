"""
NutriApp Backend - FastAPI
Multi-tenant nutrition management platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import auth, patients, anthropometrics, meal_plans, dashboard, pautas

# Import database
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 NutriApp Backend Starting...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")

    # Run migrations for existing tables
    from sqlalchemy import text
    migrations = [
        # patients
        "ALTER TABLE patients ALTER COLUMN sex TYPE VARCHAR(20)",
        # anthropometrics — add all ISAK columns that may be missing
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS arm_relaxed_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS arm_contracted_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS hip_glute_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS thigh_max_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS thigh_mid_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS calf_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS triceps_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS subscapular_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS biceps_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS iliac_crest_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS supraspinal_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS abdominal_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS medial_thigh_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS max_calf_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS pectoral_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS axillary_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS front_thigh_mm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS head_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS neck_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS chest_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS ankle_min_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS humerus_width_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS femur_width_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS biacromial_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS biiliocrestal_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS ap_chest_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS transv_chest_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS foot_length_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS wrist_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS ankle_bimalleolar_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS acromion_radial_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS radial_styloid_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS iliospinal_height_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS trochanter_tibial_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS body_density FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS fat_mass_pct FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS fat_mass_kg FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS lean_mass_kg FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS sum_6_skinfolds FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS somatotype_endo FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS somatotype_meso FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS somatotype_ecto FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS isak_level VARCHAR(20)",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except Exception:
                pass
        conn.commit()
    print("✅ Migrations complete")

    yield
    print("🛑 NutriApp Backend Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="NutriApp API",
    description="Multi-tenant nutrition management platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://nutricionista-app.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(anthropometrics.router)
app.include_router(meal_plans.router)
app.include_router(dashboard.router)
app.include_router(pautas.router)


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "NutriApp Backend v0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
