"""
NutriApp Backend - FastAPI
Multi-tenant nutrition management platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import auth, patients, anthropometrics, meal_plans, dashboard, pautas, settings, antecedentes, recetas, alimentos, appointments, portal

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
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS tibiale_height_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS arm_span_cm FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS body_density FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS fat_mass_pct FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS fat_mass_kg FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS lean_mass_kg FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS sum_6_skinfolds FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS somatotype_endo FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS somatotype_meso FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS somatotype_ecto FLOAT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS isak_level VARCHAR(20)",
        # patients
        "ALTER TABLE patients ADD COLUMN IF NOT EXISTS allergies TEXT",
        # nutritionists — branding fields
        "ALTER TABLE nutritionists ADD COLUMN IF NOT EXISTS clinic_name VARCHAR(255)",
        "ALTER TABLE nutritionists ADD COLUMN IF NOT EXISTS report_tagline VARCHAR(500)",
        "ALTER TABLE nutritionists ADD COLUMN IF NOT EXISTS logo_base64 TEXT",
        # pautas
        "ALTER TABLE pautas ADD COLUMN IF NOT EXISTS menu_json TEXT",
        "ALTER TABLE pautas ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE",
        # antecedentes
        """CREATE TABLE IF NOT EXISTS antecedentes (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER UNIQUE NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            identidad_genero VARCHAR,
            estado_civil VARCHAR,
            prevision VARCHAR,
            horario_trabajo VARCHAR,
            tipo_traslado VARCHAR,
            nutricionista_previo BOOLEAN,
            observacion_nutricionista_previo TEXT,
            motivo_consulta TEXT,
            tipo_alimentacion VARCHAR,
            peso_habitual FLOAT,
            peso_maximo FLOAT,
            peso_minimo FLOAT,
            peso_oscilaciones TEXT,
            enfermedades_preexistentes TEXT,
            antecedentes_familiares TEXT,
            farmacos_suplementos TEXT,
            suplementacion_b12 TEXT,
            cirugias TEXT,
            dietas_moda TEXT,
            tabaco_alcohol TEXT,
            ejercicio_frecuencia VARCHAR,
            ejercicio_duracion VARCHAR,
            ejercicio_intensidad VARCHAR,
            ejercicio_objetivo TEXT,
            observacion_actividad_fisica TEXT,
            con_quien_vive VARCHAR,
            mascotas VARCHAR,
            relacion_familiar TEXT,
            quien_cocina VARCHAR,
            gusta_cocinar BOOLEAN,
            sale_fines_semana BOOLEAN,
            transito_intestinal TEXT,
            sintomas_gi TEXT,
            evento_traumatico TEXT,
            intolerancias TEXT,
            aversiones TEXT,
            alimentos_gustados TEXT,
            comida_emocional TEXT,
            tiempo_comidas VARCHAR,
            come_distracciones BOOLEAN,
            calificacion_alimentacion INTEGER,
            recordatorio_semana TEXT,
            recordatorio_finde TEXT,
            metas_corto_plazo TEXT,
            metas_largo_plazo TEXT,
            signos_carenciales TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        "ALTER TABLE antecedentes ADD COLUMN IF NOT EXISTS observacion_nutricionista_previo TEXT",
        "ALTER TABLE antecedentes ADD COLUMN IF NOT EXISTS observacion_actividad_fisica TEXT",
        "CREATE INDEX IF NOT EXISTS ix_antecedentes_patient_id ON antecedentes (patient_id)",
        # audit_logs
        """CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            nutritionist_id INTEGER REFERENCES nutritionists(id),
            action VARCHAR(50),
            resource VARCHAR(50),
            resource_id INTEGER,
            detail VARCHAR(500),
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_nutritionist_id ON audit_logs (nutritionist_id)",
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at)",
        # recetas
        """CREATE TABLE IF NOT EXISTS recetas (
            id SERIAL PRIMARY KEY,
            nutritionist_id INTEGER REFERENCES nutritionists(id) ON DELETE CASCADE,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            categoria VARCHAR(100) DEFAULT 'General',
            porciones_rinde INTEGER DEFAULT 1,
            notas TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_recetas_nutritionist_id ON recetas (nutritionist_id)",
        """CREATE TABLE IF NOT EXISTS receta_ingredientes (
            id SERIAL PRIMARY KEY,
            receta_id INTEGER REFERENCES recetas(id) ON DELETE CASCADE,
            nombre_alimento VARCHAR(255) NOT NULL,
            gramos FLOAT DEFAULT 100,
            medida_casera VARCHAR(100),
            calorias FLOAT DEFAULT 0,
            proteinas_g FLOAT DEFAULT 0,
            carbohidratos_g FLOAT DEFAULT 0,
            grasas_g FLOAT DEFAULT 0,
            fibra_g FLOAT DEFAULT 0
        )""",
        "CREATE INDEX IF NOT EXISTS ix_receta_ingredientes_receta_id ON receta_ingredientes (receta_id)",
        """CREATE TABLE IF NOT EXISTS receta_equivalencias (
            id SERIAL PRIMARY KEY,
            receta_id INTEGER REFERENCES recetas(id) ON DELETE CASCADE,
            grupo VARCHAR(100) NOT NULL,
            porciones FLOAT DEFAULT 0
        )""",
        "CREATE INDEX IF NOT EXISTS ix_receta_equivalencias_receta_id ON receta_equivalencias (receta_id)",
        # appointments
        """CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    nutritionist_id INTEGER REFERENCES nutritionists(id) ON DELETE CASCADE,
    patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 45,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)""",
        "CREATE INDEX IF NOT EXISTS ix_appointments_nutritionist_id ON appointments (nutritionist_id)",
        "CREATE INDEX IF NOT EXISTS ix_appointments_scheduled_at ON appointments (scheduled_at)",
        "CREATE INDEX IF NOT EXISTS ix_appointments_patient_id ON appointments (patient_id)",
        # patient_share_tokens
        """CREATE TABLE IF NOT EXISTS patient_share_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) UNIQUE NOT NULL,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    nutritionist_id INTEGER REFERENCES nutritionists(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE
)""",
        "CREATE INDEX IF NOT EXISTS ix_patient_share_tokens_token ON patient_share_tokens (token)",
        "CREATE INDEX IF NOT EXISTS ix_patient_share_tokens_patient_id ON patient_share_tokens (patient_id)",
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

# CORS configuration — add FRONTEND_URL env var in production
_extra = os.getenv("FRONTEND_URL", "")
origins = list(filter(None, [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://nutricionista-app.vercel.app",
    _extra,
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting (in-memory, per IP) ────────────────────────────────────────
_rate_store: dict[str, list[datetime]] = defaultdict(list)
RATE_LIMIT_ROUTES = {"/auth/login", "/auth/register"}
RATE_WINDOW = 60   # seconds
RATE_MAX    = 10   # requests per window
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_ENABLED and request.url.path in RATE_LIMIT_ROUTES:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=RATE_WINDOW)
        _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]
        if len(_rate_store[ip]) >= RATE_MAX:
            return JSONResponse(status_code=429, content={"detail": "Demasiados intentos. Espera un momento."})
        _rate_store[ip].append(now)
    return await call_next(request)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(anthropometrics.router)
app.include_router(meal_plans.router)
app.include_router(dashboard.router)
app.include_router(pautas.router)
app.include_router(settings.router)
app.include_router(antecedentes.router)
app.include_router(recetas.router)
app.include_router(alimentos.router)
app.include_router(appointments.router)
app.include_router(portal.router)


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
