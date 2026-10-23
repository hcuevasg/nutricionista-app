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
import asyncio
import logging
import os
import re
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import auth, errors, notas, patients, anthropometrics, dashboard, plantillas, pautas, settings, antecedentes, recetas, alimentos, appointments, portal

# Import database
from database import engine, Base
import backup_r2
import error_log
from routers.errors import user_id_from_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 NutriApp Backend Starting...")
    from sqlalchemy import text
    # Si la base no responde, no se intentan las ~70 migraciones una por una:
    # el arranque se demoraría más que el healthcheck de Railway.
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"⚠️ Base de datos no disponible, se omiten tablas y migraciones: {e}")
        yield
        return
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")

    # Run migrations for existing tables
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
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS goals_text TEXT",
        "ALTER TABLE anthropometrics ADD COLUMN IF NOT EXISTS next_eval_date VARCHAR",
        # patients
        "ALTER TABLE patients ADD COLUMN IF NOT EXISTS allergies TEXT",
        # nutritionists — branding fields
        "ALTER TABLE nutritionists ADD COLUMN IF NOT EXISTS clinic_name VARCHAR(255)",
        "ALTER TABLE nutritionists ADD COLUMN IF NOT EXISTS report_tagline VARCHAR(500)",
        "ALTER TABLE nutritionists ADD COLUMN IF NOT EXISTS logo_base64 TEXT",
        # pautas
        "ALTER TABLE pautas ADD COLUMN IF NOT EXISTS menu_json TEXT",
        "ALTER TABLE pautas ADD COLUMN is_active BOOLEAN DEFAULT FALSE",
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
    # Una transacción por sentencia: en Postgres un error aborta la transacción
    # completa, así que una migración fallida no debe arrastrar a las siguientes.
    failed = 0
    for sql in migrations:
        try:
            with engine.begin() as conn:
                conn.execute(text(sql))
        except Exception:
            failed += 1
    print(f"✅ Migrations complete ({len(migrations) - failed} aplicadas, {failed} omitidas)")

    # Migraciones versionadas (Alembic): los cambios de esquema nuevos van en
    # backend/migrations/versions, no en la lista de arriba.
    try:
        from alembic import command
        from alembic.config import Config
        cfg = Config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "alembic.ini"))
        cfg.set_main_option("script_location",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations"))
        command.upgrade(cfg, "head")
        print("✅ Alembic: esquema en la última versión")
    except Exception as e:
        print(f"⚠️ Alembic no pudo actualizar el esquema: {e}")

    # Catálogo de alimentos integrado (solo si la tabla está vacía)
    from database import SessionLocal
    from routers.alimentos import seed_alimentos
    seed_db = SessionLocal()
    try:
        n = seed_alimentos(seed_db)
        if n:
            print(f"✅ Alimentos cargados: {n}")
    except Exception as e:
        print(f"⚠️ No se pudieron cargar los alimentos: {e}")
    finally:
        seed_db.close()

    # Backups automáticos cifrados a Cloudflare R2 (solo si están configurados)
    backup_task = None
    if backup_r2.configured():
        backup_task = asyncio.create_task(backup_r2.scheduler())
        print("✅ Backups automáticos a R2 activados")
    else:
        print("ℹ️ Backups automáticos a R2 desactivados (faltan variables R2_* / BACKUP_ENCRYPTION_KEY)")

    yield
    if backup_task:
        backup_task.cancel()
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

@app.middleware("http")
async def error_log_middleware(request: Request, call_next):
    """Registra los errores no controlados. Se declara antes de CORS para que la
    respuesta 500 también lleve los headers CORS y el frontend pueda leerla."""
    try:
        return await call_next(request)
    except Exception as exc:
        logging.getLogger("nutriapp").exception("Error no controlado en %s %s", request.method, request.url.path)
        header = request.headers.get("authorization", "")
        ref = error_log.record(
            "backend",
            nutritionist_id=user_id_from_token(header[7:] if header.lower().startswith("bearer ") else None),
            method=request.method, path=request.url.path, error_type=type(exc).__name__, message=str(exc),
            stack="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            user_agent=request.headers.get("user-agent"),
        )
        detail = "Error interno del servidor" + (f" (ref. {ref})" if ref else "")
        return JSONResponse(status_code=500, content={"detail": detail})


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting (in-memory, per IP) ────────────────────────────────────────
_rate_store: dict[str, list[datetime]] = defaultdict(list)
RATE_WINDOW = 60   # seconds
# (bucket, regex de ruta, máximo de requests por ventana y por IP)
RATE_LIMIT_RULES = [
    ("auth",   re.compile(r"^/auth/(login|register|2fa/verify)$"), 10),
    ("errors", re.compile(r"^/errors/report$"), 20),
    ("ai",     re.compile(r"^/pautas/\d+/\d+/(generar-menu|generar-menu-stream|ai-suggest)$"), 10),
    # Portal público: 3 requests por carga de página
    ("portal", re.compile(r"^/portal/(?!tokens(/|$))[^/]+(/(pautas|evaluations|consent))?$"), 60),
]
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"


def _client_ip(request: Request) -> str:
    # El proxy de Railway agrega la IP real al final de X-Forwarded-For; las
    # entradas anteriores las controla el cliente y se pueden falsificar.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_ENABLED and request.method != "OPTIONS":
        path = request.url.path
        for bucket, pattern, max_requests in RATE_LIMIT_RULES:
            if not pattern.match(path):
                continue
            key = f"{bucket}:{_client_ip(request)}"
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=RATE_WINDOW)
            hits = [t for t in _rate_store[key] if t > window_start]
            if len(hits) >= max_requests:
                _rate_store[key] = hits
                return JSONResponse(status_code=429, content={"detail": "Demasiadas solicitudes. Espera un momento."})
            hits.append(now)
            _rate_store[key] = hits
            break
    return await call_next(request)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(anthropometrics.router)
app.include_router(dashboard.router)
app.include_router(pautas.router)
app.include_router(settings.router)
app.include_router(antecedentes.router)
app.include_router(recetas.router)
app.include_router(alimentos.router)
app.include_router(appointments.router)
app.include_router(portal.router)
app.include_router(plantillas.router)
app.include_router(errors.router)
app.include_router(notas.router)


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
