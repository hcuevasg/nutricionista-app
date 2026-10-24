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
from routers import auth, errors, laboratorio, notas, patients, anthropometrics, dashboard, plantillas, pautas, settings, antecedentes, recetas, alimentos, appointments, portal

# Import database
from database import engine, Base
import backup_r2
import crypto_fields
import error_log
from routers.errors import user_id_from_token
from auth import is_production
from timeutil import utcnow


DB_WAIT_SECONDS = 60


def _database_ready() -> bool:
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _wait_for_database(seconds: float) -> bool:
    """Railway puede levantar el backend antes de que Postgres acepte conexiones:
    se reintenta en vez de arrancar sin migraciones ni cifrado."""
    deadline = asyncio.get_running_loop().time() + seconds
    while True:
        if await asyncio.to_thread(_database_ready):
            return True
        if asyncio.get_running_loop().time() >= deadline:
            return False
        await asyncio.sleep(3)


async def _prepare_when_database_returns() -> None:
    """Si la base no estaba al arrancar, prepara el esquema apenas vuelva."""
    while not await _wait_for_database(30):
        print("⚠️ La base de datos sigue sin responder; se reintenta")
    await asyncio.to_thread(_prepare_database)


def _prepare_database() -> None:
    """Tablas, migraciones (heredadas + Alembic), cifrado de datos y catálogo de alimentos."""
    from sqlalchemy import text
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

    # Cifrado de datos de salud: cifra lo que aún esté en texto plano
    if crypto_fields.enabled():
        try:
            n = crypto_fields.encrypt_existing(engine, Base)
            print(f"✅ Datos sensibles cifrados{f' ({n} valores existentes)' if n else ''}")
        except Exception as e:
            print(f"⚠️ No se pudieron cifrar los datos existentes: {e}")
    elif is_production():
        print("⚠️ DATA_ENCRYPTION_KEY no configurada: los datos de salud se guardan sin cifrar")

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 NutriApp Backend Starting...")
    prepare_task = None
    if await _wait_for_database(DB_WAIT_SECONDS):
        await asyncio.to_thread(_prepare_database)
    else:
        print("⚠️ Base de datos no disponible: el esquema se preparará cuando vuelva")
        prepare_task = asyncio.create_task(_prepare_when_database_returns())

    # Backups automáticos cifrados a Cloudflare R2 (solo si están configurados)
    backup_task = None
    if backup_r2.configured():
        backup_task = asyncio.create_task(backup_r2.scheduler())
        print("✅ Backups automáticos a R2 activados")
    else:
        print("ℹ️ Backups automáticos a R2 desactivados (faltan variables R2_* / BACKUP_ENCRYPTION_KEY)")

    yield
    for task in (backup_task, prepare_task):
        if task:
            task.cancel()
    print("🛑 NutriApp Backend Shutting down...")


# Create FastAPI app
# La documentación interactiva del API solo en desarrollo (ENABLE_API_DOCS=true la habilita)
_docs = os.getenv("ENABLE_API_DOCS", "").lower() == "true" or not is_production()
app = FastAPI(
    title="NutriApp API",
    description="Multi-tenant nutrition management platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs else None,
    redoc_url="/redoc" if _docs else None,
    openapi_url="/openapi.json" if _docs else None,
)

# CORS: solo el frontend publicado (y localhost en desarrollo). FRONTEND_URL agrega otro dominio.
origins = list(filter(None, [
    "https://nutricionista-app.vercel.app",
    os.getenv("FRONTEND_URL", ""),
    *([] if is_production() else ["http://localhost:3000", "http://localhost:5173"]),
]))

@app.middleware("http")
async def error_log_middleware(request: Request, call_next):
    """Registra los errores no controlados. CORS es la capa más externa (se agrega
    al final), así la respuesta 500 también lleva sus headers y el frontend la lee."""
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


# ── Rate limiting (in-memory, per IP) ────────────────────────────────────────
_rate_store: dict[str, list[datetime]] = defaultdict(list)
RATE_WINDOW = 60   # seconds
# (bucket, regex de ruta, máximo de requests por ventana y por IP). Se aplica la
# primera regla que calce y, además, el límite general.
RATE_LIMIT_RULES = [
    ("auth",   re.compile(r"^/auth/(login|register|2fa/verify)$"), 10),
    # Acciones sensibles de la cuenta y descargas/cargas completas de datos
    ("sensitive", re.compile(r"^/(auth/(password|logout-all|2fa/(setup|enable|disable))"
                             r"|settings/(backup|restore)|patients/\d+/export)$"), 10),
    ("errors", re.compile(r"^/errors/report$"), 20),
    ("ai",     re.compile(r"^/pautas/\d+/\d+/(generar-menu|generar-menu-stream|ai-suggest)$"), 10),
    # Portal público: 3 requests por carga de página
    ("portal", re.compile(r"^/portal/(?!tokens(/|$))[^/]+(/(pautas|evaluations|consent))?$"), 60),
]
GLOBAL_RATE_LIMIT = 300   # cualquier ruta, por IP y minuto: frena scrapers y bots
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"


def _client_ip(request: Request) -> str:
    # El proxy de Railway agrega la IP real al final de X-Forwarded-For; las
    # entradas anteriores las controla el cliente y se pueden falsificar.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def _hit(key: str, max_requests: int) -> bool:
    """Registra una request en la ventana; False si supera el máximo."""
    now = utcnow()
    hits = [t for t in _rate_store[key] if t > now - timedelta(seconds=RATE_WINDOW)]
    if len(hits) >= max_requests:
        _rate_store[key] = hits
        return False
    hits.append(now)
    _rate_store[key] = hits
    return True


def _purge_rate_store() -> None:
    """Olvida las IPs sin actividad reciente para que la memoria no crezca sin límite."""
    if len(_rate_store) < 5000:
        return
    cutoff = utcnow() - timedelta(seconds=RATE_WINDOW)
    for key in [k for k, v in _rate_store.items() if not v or v[-1] <= cutoff]:
        del _rate_store[key]


_TOO_MANY = {"detail": "Demasiadas solicitudes. Espera un momento."}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_ENABLED and request.method != "OPTIONS" and request.url.path != "/health":
        _purge_rate_store()
        path, ip = request.url.path, _client_ip(request)
        for bucket, pattern, max_requests in RATE_LIMIT_RULES:
            if pattern.match(path):
                if not _hit(f"{bucket}:{ip}", max_requests):
                    return JSONResponse(status_code=429, content=_TOO_MANY)
                break
        if not _hit(f"global:{ip}", GLOBAL_RATE_LIMIT):
            return JSONResponse(status_code=429, content=_TOO_MANY)
    return await call_next(request)

# ── Tamaño máximo de las requests ────────────────────────────────────────────
MAX_BODY_BYTES = 1024 * 1024                       # 1 MB: formularios, logo (≤500 KB)
BODY_LIMITS = {"/settings/restore": 25 * 1024 * 1024}  # backup completo de la cuenta


class BodySizeLimitMiddleware:
    """Rechaza cuerpos más grandes que el límite antes de leerlos (413), y los que
    llegan sin Content-Length (411), para que nadie agote la memoria del servidor."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] in ("POST", "PUT", "PATCH"):
            headers = dict(scope["headers"])
            limit = BODY_LIMITS.get(scope["path"], MAX_BODY_BYTES)
            length = headers.get(b"content-length")
            status, detail = None, None
            if length is None:
                if b"transfer-encoding" in headers:
                    status, detail = 411, "Falta Content-Length"
            elif not length.isdigit() or int(length) > limit:
                status, detail = 413, f"La solicitud supera el máximo de {limit // (1024 * 1024)} MB"
            if status:
                response = JSONResponse(status_code=status, content={"detail": detail})
                return await response(scope, receive, send)
        return await self.app(scope, receive, send)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Headers de seguridad en todas las respuestas del API. Las respuestas traen
    datos de salud: no se guardan en cachés del navegador ni de proxies."""
    response = await call_next(request)
    h = response.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("X-Frame-Options", "DENY")
    h.setdefault("Referrer-Policy", "no-referrer")
    h.setdefault("Cache-Control", "no-store")
    if not request.url.path.startswith(("/docs", "/redoc")):
        h.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    if is_production():
        h.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
    return response


app.add_middleware(BodySizeLimitMiddleware)
# Se agrega al final para ser la capa más externa: los 413/429/500 también llevan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # la sesión va en el header Authorization, no en cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)

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
app.include_router(laboratorio.router)


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
