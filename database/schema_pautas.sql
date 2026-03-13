-- Tablas del módulo de Pautas de Alimentación
-- Ejecutar sobre nutricionista.db  (ya integrado en db_manager.py → initialize_db)

-- Pauta principal
CREATE TABLE IF NOT EXISTS pautas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id         INTEGER NOT NULL,
    fecha_creacion      TEXT NOT NULL,          -- ISO  YYYY-MM-DD
    tipo_pauta          TEXT NOT NULL,          -- omnivoro | ovolacto | vegano | pescetariano | sin_gluten
    nombre_pauta        TEXT,
    -- Datos de cálculo
    peso_calculo        REAL NOT NULL,
    -- Requerimientos calculados
    tmb                 REAL,
    fa                  REAL,
    fa_key              TEXT,                   -- clave del factor (sedentaria, liviana…)
    get                 REAL,
    prot_gr_kg          REAL,
    prot_total_g        REAL,
    prot_total_kcal     REAL,
    prot_pct            REAL,
    lip_pct             REAL,
    lip_total_kcal      REAL,
    lip_total_g         REAL,
    cho_total_kcal      REAL,
    cho_total_g         REAL,
    cho_g_kg            REAL,
    -- Tabla de equivalencias seleccionada para el PDF
    tabla_equivalencias TEXT,
    incluir_equivalencias INTEGER DEFAULT 1,
    observaciones       TEXT,
    FOREIGN KEY (paciente_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Porciones totales del día por grupo
CREATE TABLE IF NOT EXISTS pauta_porciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pauta_id    INTEGER NOT NULL,
    grupo       TEXT    NOT NULL,
    porciones   REAL    DEFAULT 0,
    FOREIGN KEY (pauta_id) REFERENCES pautas(id) ON DELETE CASCADE
);

-- Distribución de porciones por tiempo de comida
CREATE TABLE IF NOT EXISTS pauta_distribucion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pauta_id        INTEGER NOT NULL,
    tiempo_comida   TEXT    NOT NULL,   -- desayuno | colacion1 | colacion2 | almuerzo | once | cena
    grupo           TEXT    NOT NULL,
    porciones       REAL    DEFAULT 0,
    FOREIGN KEY (pauta_id) REFERENCES pautas(id) ON DELETE CASCADE
);
