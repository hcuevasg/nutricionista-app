import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nutricionista.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            birth_date  TEXT,
            age         INTEGER,
            sex         TEXT,
            height_cm   REAL,
            weight_kg   REAL,
            phone       TEXT,
            email       TEXT,
            address     TEXT,
            occupation  TEXT,
            notes       TEXT,
            created_at  TEXT    DEFAULT (datetime('now','localtime')),
            updated_at  TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS anthropometrics (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id          INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            date                TEXT    NOT NULL,
            session_date        TEXT,
            -- Datos básicos
            weight_kg           REAL,
            height_cm           REAL,
            waist_cm            REAL,
            -- Perímetros (cm)
            arm_relaxed_cm      REAL,
            arm_contracted_cm   REAL,
            hip_glute_cm        REAL,
            thigh_max_cm        REAL,
            thigh_mid_cm        REAL,
            calf_cm             REAL,
            -- Pliegues cutáneos (mm)
            triceps_mm          REAL,
            subscapular_mm      REAL,
            biceps_mm           REAL,
            iliac_crest_mm      REAL,
            supraspinal_mm      REAL,
            abdominal_mm        REAL,
            medial_thigh_mm     REAL,
            max_calf_mm         REAL,
            -- Calculados
            sum_6_skinfolds     REAL,
            body_density        REAL,
            fat_mass_pct        REAL,
            fat_mass_kg         REAL,
            lean_mass_kg        REAL,
            -- Campos heredados (compatibilidad)
            bmi                 REAL,
            ideal_weight_kg     REAL,
            bmr                 REAL,
            tdee                REAL,
            body_fat_pct        REAL,
            activity_level      TEXT,
            -- Nivel ISAK
            isak_level          TEXT DEFAULT 'ISAK 1',
            -- ISAK 2 — pliegues adicionales (mm)
            pectoral_mm         REAL,
            axillary_mm         REAL,
            front_thigh_mm      REAL,
            -- ISAK 2 — perímetros adicionales (cm)
            head_cm             REAL,
            neck_cm             REAL,
            chest_cm            REAL,
            ankle_min_cm        REAL,
            -- ISAK 2 — diámetros óseos (cm)
            humerus_width_cm    REAL,
            femur_width_cm      REAL,
            biacromial_cm       REAL,
            biiliocrestal_cm    REAL,
            ap_chest_cm         REAL,
            transv_chest_cm     REAL,
            foot_length_cm      REAL,
            wrist_cm            REAL,
            ankle_bimalleolar_cm REAL,
            -- ISAK 2 — longitudes (cm)
            acromion_radial_cm  REAL,
            radial_styloid_cm   REAL,
            iliospinal_height_cm REAL,
            trochanter_tibial_cm REAL,
            -- ISAK 2 — calculados
            somatotype_endo     REAL,
            somatotype_meso     REAL,
            somatotype_ecto     REAL,
            waist_height_ratio  REAL,
            arm_muscle_area     REAL,
            created_at          TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS meal_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            goal        TEXT,
            calories    REAL,
            protein_g   REAL,
            carbs_g     REAL,
            fat_g       REAL,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS meal_items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id      INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
            meal_type    TEXT    NOT NULL,
            food_name    TEXT    NOT NULL,
            quantity     REAL,
            unit         TEXT,
            calories     REAL,
            protein_g    REAL,
            carbs_g      REAL,
            fat_g        REAL,
            fiber_g      REAL
        );

        CREATE TABLE IF NOT EXISTS alimentos_db (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_es       TEXT NOT NULL,
            nombre_en       TEXT,
            calorias        REAL NOT NULL DEFAULT 0,
            proteinas_g     REAL NOT NULL DEFAULT 0,
            carbohidratos_g REAL NOT NULL DEFAULT 0,
            grasas_g        REAL NOT NULL DEFAULT 0,
            fibra_g         REAL NOT NULL DEFAULT 0,
            azucares_g      REAL,
            sodio_mg        REAL,
            calcio_mg       REAL,
            hierro_mg       REAL,
            vitamina_c_mg   REAL,
            vitamina_a_mcg  REAL,
            fuente          TEXT DEFAULT 'USDA',
            es_personalizado INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_alimentos_es
            ON alimentos_db(nombre_es COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_alimentos_en
            ON alimentos_db(nombre_en COLLATE NOCASE);

        CREATE TABLE IF NOT EXISTS plan_templates (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            category      TEXT NOT NULL DEFAULT 'Otra',
            description   TEXT,
            calories      REAL,
            protein_g     REAL,
            carbs_g       REAL,
            fat_g         REAL,
            fiber_g       REAL,
            goal          TEXT,
            notes         TEXT,
            use_count     INTEGER NOT NULL DEFAULT 0,
            is_predefined INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS template_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL REFERENCES plan_templates(id) ON DELETE CASCADE,
            meal_type   TEXT NOT NULL,
            food_name   TEXT NOT NULL,
            quantity    REAL,
            unit        TEXT,
            calories    REAL,
            protein_g   REAL,
            carbs_g     REAL,
            fat_g       REAL,
            fiber_g     REAL
        );

        CREATE TABLE IF NOT EXISTS template_usage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL REFERENCES plan_templates(id) ON DELETE CASCADE,
            patient_id  INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            plan_id     INTEGER REFERENCES meal_plans(id) ON DELETE SET NULL,
            used_at     TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    conn.commit()
    _migrate(conn)
    conn.close()
    seed_predefined_templates()


def _migrate(conn):
    """Add any columns missing from previous schema versions."""
    new_cols = [
        # ISAK 1 original columns
        ("arm_relaxed_cm",       "REAL"),
        ("arm_contracted_cm",    "REAL"),
        ("hip_glute_cm",         "REAL"),
        ("thigh_max_cm",         "REAL"),
        ("thigh_mid_cm",         "REAL"),
        ("calf_cm",              "REAL"),
        ("triceps_mm",           "REAL"),
        ("subscapular_mm",       "REAL"),
        ("biceps_mm",            "REAL"),
        ("iliac_crest_mm",       "REAL"),
        ("supraspinal_mm",       "REAL"),
        ("abdominal_mm",         "REAL"),
        ("medial_thigh_mm",      "REAL"),
        ("max_calf_mm",          "REAL"),
        ("sum_6_skinfolds",      "REAL"),
        ("body_density",         "REAL"),
        ("fat_mass_pct",         "REAL"),
        ("fat_mass_kg",          "REAL"),
        ("lean_mass_kg",         "REAL"),
        # ISAK 2 additions
        ("isak_level",           "TEXT"),
        ("pectoral_mm",          "REAL"),
        ("axillary_mm",          "REAL"),
        ("front_thigh_mm",       "REAL"),
        ("head_cm",              "REAL"),
        ("neck_cm",              "REAL"),
        ("chest_cm",             "REAL"),
        ("ankle_min_cm",         "REAL"),
        ("humerus_width_cm",     "REAL"),
        ("femur_width_cm",       "REAL"),
        ("biacromial_cm",        "REAL"),
        ("biiliocrestal_cm",     "REAL"),
        ("ap_chest_cm",          "REAL"),
        ("transv_chest_cm",      "REAL"),
        ("foot_length_cm",       "REAL"),
        ("wrist_cm",             "REAL"),
        ("ankle_bimalleolar_cm", "REAL"),
        ("acromion_radial_cm",   "REAL"),
        ("radial_styloid_cm",    "REAL"),
        ("iliospinal_height_cm", "REAL"),
        ("trochanter_tibial_cm", "REAL"),
        ("somatotype_endo",      "REAL"),
        ("somatotype_meso",      "REAL"),
        ("somatotype_ecto",      "REAL"),
        ("waist_height_ratio",   "REAL"),
        ("arm_muscle_area",      "REAL"),
        ("session_date",         "TEXT"),
    ]
    existing = {row[1] for row in
                conn.execute("PRAGMA table_info(anthropometrics)").fetchall()}
    for col, col_type in new_cols:
        if col not in existing:
            conn.execute(
                f"ALTER TABLE anthropometrics ADD COLUMN {col} {col_type}"
            )
    # Populate session_date from date for existing records
    conn.execute(
        "UPDATE anthropometrics SET session_date = date WHERE session_date IS NULL"
    )

    # Migrate meal_items table
    meal_item_cols = [("fiber_g", "REAL")]
    existing_mi = {row[1] for row in
                   conn.execute("PRAGMA table_info(meal_items)").fetchall()}
    for col, col_type in meal_item_cols:
        if col not in existing_mi:
            conn.execute(f"ALTER TABLE meal_items ADD COLUMN {col} {col_type}")

    # Migrate meal_plans for template tracking
    meal_plan_new_cols = [("template_id", "INTEGER")]
    existing_mp = {row[1] for row in
                   conn.execute("PRAGMA table_info(meal_plans)").fetchall()}
    for col, col_type in meal_plan_new_cols:
        if col not in existing_mp:
            conn.execute(f"ALTER TABLE meal_plans ADD COLUMN {col} {col_type}")

    # Migrate patients table
    patient_new_cols = [
        ("photo_path",     "TEXT"),
        ("goal_weight_kg", "REAL"),
        ("goal_fat_pct",   "REAL"),
        ("goal_fat_kg",    "REAL"),
        ("goal_lean_kg",   "REAL"),
        ("goal_date",      "TEXT"),
    ]
    existing_p = {row[1] for row in
                  conn.execute("PRAGMA table_info(patients)").fetchall()}
    for col, col_type in patient_new_cols:
        if col not in existing_p:
            conn.execute(f"ALTER TABLE patients ADD COLUMN {col} {col_type}")
    conn.commit()


# ── Patients ─────────────────────────────────────────────────────────────────

def insert_patient(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    row = {
        "photo_path": None, "goal_weight_kg": None, "goal_fat_pct": None,
        "goal_fat_kg": None, "goal_lean_kg": None, "goal_date": None,
        **data
    }
    cur.execute("""
        INSERT INTO patients (name, birth_date, age, sex, height_cm, weight_kg,
                              phone, email, address, occupation, notes,
                              photo_path, goal_weight_kg, goal_fat_pct,
                              goal_fat_kg, goal_lean_kg, goal_date)
        VALUES (:name,:birth_date,:age,:sex,:height_cm,:weight_kg,
                :phone,:email,:address,:occupation,:notes,
                :photo_path,:goal_weight_kg,:goal_fat_pct,
                :goal_fat_kg,:goal_lean_kg,:goal_date)
    """, row)
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def update_patient(pid: int, data: dict):
    data["id"] = pid
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Ensure new fields have defaults
    data.setdefault("photo_path", None)
    data.setdefault("goal_weight_kg", None)
    data.setdefault("goal_fat_pct", None)
    data.setdefault("goal_fat_kg", None)
    data.setdefault("goal_lean_kg", None)
    data.setdefault("goal_date", None)
    conn = get_connection()
    conn.execute("""
        UPDATE patients SET name=:name, birth_date=:birth_date, age=:age,
            sex=:sex, height_cm=:height_cm, weight_kg=:weight_kg,
            phone=:phone, email=:email, address=:address,
            occupation=:occupation, notes=:notes, updated_at=:updated_at,
            photo_path=:photo_path, goal_weight_kg=:goal_weight_kg,
            goal_fat_pct=:goal_fat_pct, goal_fat_kg=:goal_fat_kg,
            goal_lean_kg=:goal_lean_kg, goal_date=:goal_date
        WHERE id=:id
    """, data)
    conn.commit()
    conn.close()


def delete_patient(pid: int):
    conn = get_connection()
    conn.execute("DELETE FROM patients WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def get_all_patients() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patients ORDER BY name COLLATE NOCASE"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patient(pid: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def search_patients(query: str) -> list:
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? ORDER BY name",
        (like, like, like)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Anthropometrics ───────────────────────────────────────────────────────────

_ANTHRO_DEFAULTS = {
    "isak_level": "ISAK 1",
    "session_date": None,
    # ISAK 1 core fields
    "weight_kg": None, "height_cm": None, "waist_cm": None,
    "arm_relaxed_cm": None, "arm_contracted_cm": None, "hip_glute_cm": None,
    "thigh_max_cm": None, "thigh_mid_cm": None, "calf_cm": None,
    "triceps_mm": None, "subscapular_mm": None, "biceps_mm": None,
    "iliac_crest_mm": None, "supraspinal_mm": None, "abdominal_mm": None,
    "medial_thigh_mm": None, "max_calf_mm": None,
    "sum_6_skinfolds": None, "body_density": None,
    "fat_mass_pct": None, "fat_mass_kg": None, "lean_mass_kg": None,
    # ISAK 2 extra skinfolds
    "pectoral_mm": None, "axillary_mm": None, "front_thigh_mm": None,
    # ISAK 2 extra perimeters
    "head_cm": None, "neck_cm": None, "chest_cm": None, "ankle_min_cm": None,
    # ISAK 2 bone diameters
    "humerus_width_cm": None, "femur_width_cm": None,
    "biacromial_cm": None, "biiliocrestal_cm": None,
    "ap_chest_cm": None, "transv_chest_cm": None,
    "foot_length_cm": None, "wrist_cm": None, "ankle_bimalleolar_cm": None,
    # ISAK 2 lengths
    "acromion_radial_cm": None, "radial_styloid_cm": None,
    "iliospinal_height_cm": None, "trochanter_tibial_cm": None,
    # ISAK 2 calculated
    "somatotype_endo": None, "somatotype_meso": None, "somatotype_ecto": None,
    "waist_height_ratio": None, "arm_muscle_area": None,
}


def insert_anthropometric(data: dict) -> int:
    row = {**_ANTHRO_DEFAULTS, **data}
    # date = system timestamp (fecha_registro); session_date = real session date
    if not row.get("date"):
        row["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not row.get("session_date"):
        row["session_date"] = row["date"]
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO anthropometrics (
            patient_id, date, session_date, isak_level,
            weight_kg, height_cm, waist_cm,
            arm_relaxed_cm, arm_contracted_cm, hip_glute_cm,
            thigh_max_cm, thigh_mid_cm, calf_cm,
            triceps_mm, subscapular_mm, biceps_mm, iliac_crest_mm,
            supraspinal_mm, abdominal_mm, medial_thigh_mm, max_calf_mm,
            sum_6_skinfolds, body_density, fat_mass_pct, fat_mass_kg, lean_mass_kg,
            pectoral_mm, axillary_mm, front_thigh_mm,
            head_cm, neck_cm, chest_cm, ankle_min_cm,
            humerus_width_cm, femur_width_cm, biacromial_cm, biiliocrestal_cm,
            ap_chest_cm, transv_chest_cm, foot_length_cm, wrist_cm, ankle_bimalleolar_cm,
            acromion_radial_cm, radial_styloid_cm, iliospinal_height_cm, trochanter_tibial_cm,
            somatotype_endo, somatotype_meso, somatotype_ecto, waist_height_ratio, arm_muscle_area
        ) VALUES (
            :patient_id, :date, :session_date, :isak_level,
            :weight_kg, :height_cm, :waist_cm,
            :arm_relaxed_cm, :arm_contracted_cm, :hip_glute_cm,
            :thigh_max_cm, :thigh_mid_cm, :calf_cm,
            :triceps_mm, :subscapular_mm, :biceps_mm, :iliac_crest_mm,
            :supraspinal_mm, :abdominal_mm, :medial_thigh_mm, :max_calf_mm,
            :sum_6_skinfolds, :body_density, :fat_mass_pct, :fat_mass_kg, :lean_mass_kg,
            :pectoral_mm, :axillary_mm, :front_thigh_mm,
            :head_cm, :neck_cm, :chest_cm, :ankle_min_cm,
            :humerus_width_cm, :femur_width_cm, :biacromial_cm, :biiliocrestal_cm,
            :ap_chest_cm, :transv_chest_cm, :foot_length_cm, :wrist_cm, :ankle_bimalleolar_cm,
            :acromion_radial_cm, :radial_styloid_cm, :iliospinal_height_cm, :trochanter_tibial_cm,
            :somatotype_endo, :somatotype_meso, :somatotype_ecto, :waist_height_ratio, :arm_muscle_area
        )
    """, row)
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def get_anthropometrics(patient_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM anthropometrics WHERE patient_id=? ORDER BY COALESCE(session_date, date) ASC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_anthropometric(data: dict):
    """Update all fields of an existing anthropometric record. data must include 'id'."""
    conn = get_connection()
    conn.execute("""
        UPDATE anthropometrics SET
            session_date=:session_date, isak_level=:isak_level,
            weight_kg=:weight_kg, height_cm=:height_cm, waist_cm=:waist_cm,
            arm_relaxed_cm=:arm_relaxed_cm, arm_contracted_cm=:arm_contracted_cm,
            hip_glute_cm=:hip_glute_cm, thigh_max_cm=:thigh_max_cm,
            thigh_mid_cm=:thigh_mid_cm, calf_cm=:calf_cm,
            triceps_mm=:triceps_mm, subscapular_mm=:subscapular_mm,
            biceps_mm=:biceps_mm, iliac_crest_mm=:iliac_crest_mm,
            supraspinal_mm=:supraspinal_mm, abdominal_mm=:abdominal_mm,
            medial_thigh_mm=:medial_thigh_mm, max_calf_mm=:max_calf_mm,
            pectoral_mm=:pectoral_mm, axillary_mm=:axillary_mm,
            front_thigh_mm=:front_thigh_mm,
            head_cm=:head_cm, neck_cm=:neck_cm, chest_cm=:chest_cm,
            ankle_min_cm=:ankle_min_cm,
            humerus_width_cm=:humerus_width_cm, femur_width_cm=:femur_width_cm,
            biacromial_cm=:biacromial_cm, biiliocrestal_cm=:biiliocrestal_cm,
            ap_chest_cm=:ap_chest_cm, transv_chest_cm=:transv_chest_cm,
            foot_length_cm=:foot_length_cm, wrist_cm=:wrist_cm,
            ankle_bimalleolar_cm=:ankle_bimalleolar_cm,
            acromion_radial_cm=:acromion_radial_cm,
            radial_styloid_cm=:radial_styloid_cm,
            iliospinal_height_cm=:iliospinal_height_cm,
            trochanter_tibial_cm=:trochanter_tibial_cm,
            sum_6_skinfolds=:sum_6_skinfolds, body_density=:body_density,
            fat_mass_pct=:fat_mass_pct, fat_mass_kg=:fat_mass_kg,
            lean_mass_kg=:lean_mass_kg,
            somatotype_endo=:somatotype_endo, somatotype_meso=:somatotype_meso,
            somatotype_ecto=:somatotype_ecto,
            waist_height_ratio=:waist_height_ratio, arm_muscle_area=:arm_muscle_area
        WHERE id=:id
    """, data)
    conn.commit()
    conn.close()


def update_session_date(aid: int, session_date: str):
    conn = get_connection()
    conn.execute(
        "UPDATE anthropometrics SET session_date=? WHERE id=?",
        (session_date, aid)
    )
    conn.commit()
    conn.close()


def delete_anthropometric(aid: int):
    conn = get_connection()
    conn.execute("DELETE FROM anthropometrics WHERE id=?", (aid,))
    conn.commit()
    conn.close()


# ── Meal Plans ────────────────────────────────────────────────────────────────

def insert_meal_plan(data: dict) -> int:
    data.setdefault("template_id", None)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO meal_plans
            (patient_id, name, date, goal, calories, protein_g, carbs_g, fat_g, notes, template_id)
        VALUES
            (:patient_id,:name,:date,:goal,:calories,:protein_g,:carbs_g,:fat_g,:notes,:template_id)
    """, data)
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid


def update_meal_plan(mid: int, data: dict):
    data["id"] = mid
    conn = get_connection()
    conn.execute("""
        UPDATE meal_plans SET name=:name, date=:date, goal=:goal,
            calories=:calories, protein_g=:protein_g, carbs_g=:carbs_g,
            fat_g=:fat_g, notes=:notes WHERE id=:id
    """, data)
    conn.commit()
    conn.close()


def delete_meal_plan(mid: int):
    conn = get_connection()
    conn.execute("DELETE FROM meal_plans WHERE id=?", (mid,))
    conn.commit()
    conn.close()


def get_meal_plans(patient_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM meal_plans WHERE patient_id=? ORDER BY date DESC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_meal_plan(mid: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM meal_plans WHERE id=?", (mid,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Meal Items ────────────────────────────────────────────────────────────────

def insert_meal_item(data: dict) -> int:
    data.setdefault("fiber_g", None)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO meal_items (plan_id, meal_type, food_name, quantity, unit,
                                calories, protein_g, carbs_g, fat_g, fiber_g)
        VALUES (:plan_id,:meal_type,:food_name,:quantity,:unit,
                :calories,:protein_g,:carbs_g,:fat_g,:fiber_g)
    """, data)
    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return iid


def get_meal_items(plan_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM meal_items WHERE plan_id=? ORDER BY meal_type, id",
        (plan_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_meal_item(iid: int):
    conn = get_connection()
    conn.execute("DELETE FROM meal_items WHERE id=?", (iid,))
    conn.commit()
    conn.close()


def delete_all_meal_items(plan_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM meal_items WHERE plan_id=?", (plan_id,))
    conn.commit()
    conn.close()


# ── Alimentos DB ──────────────────────────────────────────────────────────────

def search_foods(query: str, limit: int = 15) -> list:
    """Search alimentos_db by Spanish or English name (LIKE, case-insensitive)."""
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        """SELECT * FROM alimentos_db
           WHERE nombre_es LIKE ? OR nombre_en LIKE ?
           ORDER BY
               CASE WHEN nombre_es LIKE ? THEN 0 ELSE 1 END,
               nombre_es COLLATE NOCASE
           LIMIT ?""",
        (like, like, f"{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_food(data: dict) -> int:
    defaults = {
        "nombre_en": None, "azucares_g": None, "sodio_mg": None,
        "calcio_mg": None, "hierro_mg": None, "vitamina_c_mg": None,
        "vitamina_a_mcg": None, "fuente": "personalizado", "es_personalizado": 1,
    }
    row = {**defaults, **data}
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alimentos_db
            (nombre_es, nombre_en, calorias, proteinas_g, carbohidratos_g,
             grasas_g, fibra_g, azucares_g, sodio_mg, calcio_mg, hierro_mg,
             vitamina_c_mg, vitamina_a_mcg, fuente, es_personalizado)
        VALUES
            (:nombre_es, :nombre_en, :calorias, :proteinas_g, :carbohidratos_g,
             :grasas_g, :fibra_g, :azucares_g, :sodio_mg, :calcio_mg, :hierro_mg,
             :vitamina_c_mg, :vitamina_a_mcg, :fuente, :es_personalizado)
    """, row)
    conn.commit()
    fid = cur.lastrowid
    conn.close()
    return fid


def get_food(food_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM alimentos_db WHERE id=?", (food_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_food(food_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM alimentos_db WHERE id=?", (food_id,))
    conn.commit()
    conn.close()


def get_foods_count() -> int:
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM alimentos_db").fetchone()[0]
    conn.close()
    return n


# ── Plan Templates ────────────────────────────────────────────────────────────

def get_all_templates() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM plan_templates ORDER BY is_predefined DESC, name COLLATE NOCASE"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_template(tid: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM plan_templates WHERE id=?", (tid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_template(data: dict) -> int:
    defaults = {
        "description": None, "calories": None, "protein_g": None,
        "carbs_g": None, "fat_g": None, "fiber_g": None,
        "goal": None, "notes": None, "use_count": 0, "is_predefined": 0,
    }
    row = {**defaults, **data}
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO plan_templates
            (name, category, description, calories, protein_g, carbs_g, fat_g,
             fiber_g, goal, notes, use_count, is_predefined)
        VALUES
            (:name,:category,:description,:calories,:protein_g,:carbs_g,:fat_g,
             :fiber_g,:goal,:notes,:use_count,:is_predefined)
    """, row)
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def update_template(tid: int, data: dict):
    data["id"] = tid
    conn = get_connection()
    conn.execute("""
        UPDATE plan_templates SET name=:name, category=:category,
            description=:description, calories=:calories, protein_g=:protein_g,
            carbs_g=:carbs_g, fat_g=:fat_g, fiber_g=:fiber_g,
            goal=:goal, notes=:notes
        WHERE id=:id
    """, data)
    conn.commit()
    conn.close()


def delete_template(tid: int):
    conn = get_connection()
    conn.execute("DELETE FROM plan_templates WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def get_template_items(tid: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM template_items WHERE template_id=? ORDER BY meal_type, id",
        (tid,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_template_item(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO template_items
            (template_id, meal_type, food_name, quantity, unit,
             calories, protein_g, carbs_g, fat_g, fiber_g)
        VALUES
            (:template_id,:meal_type,:food_name,:quantity,:unit,
             :calories,:protein_g,:carbs_g,:fat_g,:fiber_g)
    """, data)
    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return iid


def delete_template_items(tid: int):
    conn = get_connection()
    conn.execute("DELETE FROM template_items WHERE template_id=?", (tid,))
    conn.commit()
    conn.close()


def save_plan_as_template(plan_id: int, name: str,
                          category: str, description: Optional[str]) -> int:
    """Copy a meal plan and its items into plan_templates / template_items."""
    plan = get_meal_plan(plan_id)
    items = get_meal_items(plan_id)
    fiber_total = sum(i.get("fiber_g") or 0 for i in items) or None
    tid = insert_template({
        "name": name, "category": category, "description": description,
        "calories": plan.get("calories"), "protein_g": plan.get("protein_g"),
        "carbs_g": plan.get("carbs_g"), "fat_g": plan.get("fat_g"),
        "fiber_g": fiber_total, "goal": plan.get("goal"),
        "notes": plan.get("notes"),
    })
    for item in items:
        insert_template_item({
            "template_id": tid, "meal_type": item["meal_type"],
            "food_name": item["food_name"], "quantity": item.get("quantity"),
            "unit": item.get("unit"), "calories": item.get("calories"),
            "protein_g": item.get("protein_g"), "carbs_g": item.get("carbs_g"),
            "fat_g": item.get("fat_g"), "fiber_g": item.get("fiber_g"),
        })
    return tid


def apply_template_to_plan(template_id: int, plan_id: int):
    """Replace plan items with a copy of template items; increment use_count."""
    delete_all_meal_items(plan_id)
    for item in get_template_items(template_id):
        insert_meal_item({
            "plan_id": plan_id, "meal_type": item["meal_type"],
            "food_name": item["food_name"], "quantity": item.get("quantity"),
            "unit": item.get("unit"), "calories": item.get("calories"),
            "protein_g": item.get("protein_g"), "carbs_g": item.get("carbs_g"),
            "fat_g": item.get("fat_g"), "fiber_g": item.get("fiber_g"),
        })
    conn = get_connection()
    conn.execute(
        "UPDATE plan_templates SET use_count = use_count + 1 WHERE id=?",
        (template_id,)
    )
    conn.commit()
    conn.close()


def record_template_usage(template_id: int, patient_id: int,
                          plan_id: Optional[int] = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO template_usage (template_id, patient_id, plan_id) VALUES (?,?,?)",
        (template_id, patient_id, plan_id)
    )
    conn.commit()
    conn.close()


def get_template_usage(template_id: int) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT tu.used_at, p.name AS patient_name, tu.plan_id
        FROM template_usage tu
        JOIN patients p ON p.id = tu.patient_id
        WHERE tu.template_id = ?
        ORDER BY tu.used_at DESC
    """, (template_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def duplicate_template(tid: int) -> int:
    t = get_template(tid)
    items = get_template_items(tid)
    new_tid = insert_template({
        "name": f"{t['name']} (copia)", "category": t["category"],
        "description": t.get("description"), "calories": t.get("calories"),
        "protein_g": t.get("protein_g"), "carbs_g": t.get("carbs_g"),
        "fat_g": t.get("fat_g"), "fiber_g": t.get("fiber_g"),
        "goal": t.get("goal"), "notes": t.get("notes"), "is_predefined": 0,
    })
    for item in items:
        insert_template_item({
            "template_id": new_tid, "meal_type": item["meal_type"],
            "food_name": item["food_name"], "quantity": item.get("quantity"),
            "unit": item.get("unit"), "calories": item.get("calories"),
            "protein_g": item.get("protein_g"), "carbs_g": item.get("carbs_g"),
            "fat_g": item.get("fat_g"), "fiber_g": item.get("fiber_g"),
        })
    return new_tid


def set_plan_template(plan_id: int, template_id: int):
    conn = get_connection()
    conn.execute("UPDATE meal_plans SET template_id=? WHERE id=?",
                 (template_id, plan_id))
    conn.commit()
    conn.close()


def seed_predefined_templates():
    """Insert 5 predefined base templates if they don't exist yet."""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM plan_templates WHERE is_predefined=1"
    ).fetchone()[0]
    conn.close()
    if count >= 5:
        return

    _PREDEFINED = [
        {
            "meta": {
                "name": "Pauta hipocalórica 1500 kcal",
                "category": "Pérdida de peso",
                "description": "Dieta baja en calorías para pérdida de peso gradual. Rica en proteínas magras y fibra.",
                "calories": 1500, "protein_g": 110, "carbs_g": 155, "fat_g": 45,
                "fiber_g": 28, "goal": "Pérdida de peso", "is_predefined": 1,
            },
            "items": [
                ("Desayuno",      "Leche descremada",              200, "ml",  70,  7.0,  10.0,  0.4, 0.0),
                ("Desayuno",      "Avena en hojuelas",              40, "g",  152,  5.0,  27.0,  3.0, 4.0),
                ("Desayuno",      "Plátano",                       100, "g",   89,  1.1,  23.0,  0.3, 2.6),
                ("Media mañana",  "Manzana",                       150, "g",   78,  0.4,  20.0,  0.3, 3.8),
                ("Media mañana",  "Nueces",                         15, "g",   98,  2.3,   2.0,  9.6, 1.0),
                ("Almuerzo",      "Pechuga de pollo a la plancha", 150, "g",  165, 31.0,   0.0,  3.6, 0.0),
                ("Almuerzo",      "Arroz integral cocido",         100, "g",  111,  2.6,  23.0,  0.9, 1.8),
                ("Almuerzo",      "Ensalada mixta",                200, "g",   30,  2.0,   5.0,  0.3, 2.5),
                ("Almuerzo",      "Aceite de oliva",                 5, "ml",  45,  0.0,   0.0,  5.0, 0.0),
                ("Merienda",      "Yogur natural sin azúcar",      150, "g",   90,  8.0,   9.0,  2.0, 0.0),
                ("Cena",          "Merluza al horno",              150, "g",  120, 24.0,   0.0,  2.0, 0.0),
                ("Cena",          "Papa cocida",                   100, "g",   86,  2.0,  20.0,  0.1, 1.8),
                ("Cena",          "Brócoli al vapor",              150, "g",   51,  4.0,  10.0,  0.5, 3.8),
                ("Cena",          "Aceite de oliva",                 5, "ml",  45,  0.0,   0.0,  5.0, 0.0),
            ],
        },
        {
            "meta": {
                "name": "Pauta normocalórica 2000 kcal",
                "category": "Mantención",
                "description": "Alimentación equilibrada para mantener el peso corporal con buena distribución de macronutrientes.",
                "calories": 2000, "protein_g": 120, "carbs_g": 230, "fat_g": 67,
                "fiber_g": 32, "goal": "Mantenimiento", "is_predefined": 1,
            },
            "items": [
                ("Desayuno",      "Leche semidescremada",          250, "ml", 110,  9.0,  12.0,  3.0, 0.0),
                ("Desayuno",      "Pan integral",                   60, "g",  150,  6.0,  28.0,  1.5, 4.0),
                ("Desayuno",      "Huevo revuelto",                 60, "g",   86,  6.0,   0.5,  6.4, 0.0),
                ("Desayuno",      "Naranja",                       150, "g",   70,  1.3,  17.0,  0.3, 3.3),
                ("Media mañana",  "Plátano",                       120, "g",  107,  1.3,  27.0,  0.4, 3.1),
                ("Media mañana",  "Almendras",                      20, "g",  116,  4.2,   4.0, 10.0, 2.5),
                ("Almuerzo",      "Pechuga de pollo",              180, "g",  198, 37.0,   0.0,  4.3, 0.0),
                ("Almuerzo",      "Arroz integral cocido",         120, "g",  133,  3.1,  27.6,  1.1, 2.2),
                ("Almuerzo",      "Lentejas cocidas",               80, "g",   91,  6.3,  16.0,  0.3, 4.0),
                ("Almuerzo",      "Ensalada variada",              200, "g",   40,  2.0,   7.0,  0.5, 3.0),
                ("Almuerzo",      "Aceite de oliva",                 8, "ml",  72,  0.0,   0.0,  8.0, 0.0),
                ("Merienda",      "Yogur griego natural",          150, "g",  130, 11.0,   8.0,  5.0, 0.0),
                ("Merienda",      "Fresas",                        100, "g",   32,  0.7,   7.7,  0.3, 2.0),
                ("Cena",          "Salmón a la plancha",           150, "g",  233, 25.0,   0.0, 14.0, 0.0),
                ("Cena",          "Pasta integral cocida",         120, "g",  148,  5.8,  30.0,  0.9, 4.0),
                ("Cena",          "Espinacas salteadas",           150, "g",   47,  3.7,   5.7,  1.2, 2.7),
                ("Cena",          "Aceite de oliva",                 8, "ml",  72,  0.0,   0.0,  8.0, 0.0),
            ],
        },
        {
            "meta": {
                "name": "Pauta hipercalórica 2500 kcal",
                "category": "Aumento de masa",
                "description": "Dieta alta en calorías y proteínas para ganancia de masa muscular. Incluye colación adicional.",
                "calories": 2500, "protein_g": 165, "carbs_g": 280, "fat_g": 80,
                "fiber_g": 35, "goal": "Ganancia muscular", "is_predefined": 1,
            },
            "items": [
                ("Desayuno",      "Leche entera",                  300, "ml", 183,  9.9,  14.4,  9.9, 0.0),
                ("Desayuno",      "Avena en hojuelas",              70, "g",  266,  8.8,  47.0,  5.3, 7.0),
                ("Desayuno",      "Huevos revueltos",              120, "g",  172, 12.0,   1.0, 12.8, 0.0),
                ("Desayuno",      "Pan integral",                   60, "g",  150,  6.0,  28.0,  1.5, 4.0),
                ("Media mañana",  "Plátano",                       150, "g",  134,  1.6,  34.0,  0.5, 3.9),
                ("Media mañana",  "Mantequilla de maní",            30, "g",  188,  8.0,   6.0, 16.0, 2.0),
                ("Media mañana",  "Yogur griego natural",          200, "g",  173, 14.7,  10.7,  6.7, 0.0),
                ("Almuerzo",      "Carne de res magra",            200, "g",  272, 42.0,   0.0, 11.0, 0.0),
                ("Almuerzo",      "Arroz integral cocido",         150, "g",  167,  3.9,  34.5,  1.4, 2.7),
                ("Almuerzo",      "Porotos negros cocidos",        100, "g",  132,  8.9,  23.7,  0.5, 8.7),
                ("Almuerzo",      "Ensalada mixta",                200, "g",   40,  2.0,   7.0,  0.5, 3.0),
                ("Almuerzo",      "Aceite de oliva",                10, "ml",  90,  0.0,   0.0, 10.0, 0.0),
                ("Merienda",      "Batido de proteínas (whey)",     30, "g",  120, 25.0,   5.0,  1.5, 0.0),
                ("Merienda",      "Leche semidescremada",          250, "ml", 110,  9.0,  12.0,  3.0, 0.0),
                ("Merienda",      "Nueces mixtas",                  30, "g",  196,  4.5,   8.0, 17.5, 2.0),
                ("Cena",          "Pechuga de pollo",              220, "g",  242, 45.0,   0.0,  5.3, 0.0),
                ("Cena",          "Papa cocida",                   200, "g",  172,  4.0,  40.0,  0.2, 3.6),
                ("Cena",          "Brócoli al vapor",              150, "g",   51,  4.0,  10.0,  0.5, 3.8),
                ("Cena",          "Aceite de oliva",                10, "ml",  90,  0.0,   0.0, 10.0, 0.0),
                ("Colación",      "Quesillo (queso fresco)",        60, "g",   66,  9.0,   2.4,  2.4, 0.0),
                ("Colación",      "Pan integral",                   40, "g",  100,  4.0,  18.7,  1.0, 2.7),
            ],
        },
        {
            "meta": {
                "name": "Pauta vegetariana 1800 kcal",
                "category": "Vegetariana",
                "description": "Alimentación vegetariana completa sin carnes. Incluye lácteos y huevos. Rica en legumbres y vegetales.",
                "calories": 1800, "protein_g": 95, "carbs_g": 210, "fat_g": 65,
                "fiber_g": 42, "goal": "Mantenimiento", "is_predefined": 1,
            },
            "items": [
                ("Desayuno",      "Leche de soya",                 250, "ml", 108,  6.3,  12.3,  4.0, 1.3),
                ("Desayuno",      "Avena en hojuelas",              60, "g",  228,  7.5,  40.0,  4.5, 6.0),
                ("Desayuno",      "Arándanos",                     100, "g",   57,  0.7,  14.5,  0.3, 2.4),
                ("Desayuno",      "Semillas de chía",               10, "g",   49,  1.7,   4.2,  3.1, 3.4),
                ("Media mañana",  "Manzana",                       150, "g",   78,  0.4,  20.0,  0.3, 3.8),
                ("Media mañana",  "Almendras",                      25, "g",  145,  5.3,   5.0, 12.5, 3.1),
                ("Almuerzo",      "Lentejas estofadas",            150, "g",  171, 13.3,  30.0,  0.5, 10.4),
                ("Almuerzo",      "Tofu firme salteado",           100, "g",   76,  8.0,   1.9,  4.2, 0.3),
                ("Almuerzo",      "Arroz integral cocido",         100, "g",  111,  2.6,  23.0,  0.9, 1.8),
                ("Almuerzo",      "Espinacas salteadas",           150, "g",   47,  3.7,   5.7,  1.2, 2.7),
                ("Almuerzo",      "Aceite de oliva",                 8, "ml",  72,  0.0,   0.0,  8.0, 0.0),
                ("Merienda",      "Yogur natural sin azúcar",      150, "g",   90,  8.0,   9.0,  2.0, 0.0),
                ("Merienda",      "Nueces",                         20, "g",  131,  3.1,   2.8, 13.1, 1.3),
                ("Cena",          "Huevos revueltos",              120, "g",  172, 12.0,   1.0, 12.8, 0.0),
                ("Cena",          "Garbanzos cocidos",             100, "g",  164,  8.9,  27.4,  2.6, 7.6),
                ("Cena",          "Quinoa cocida",                 100, "g",  120,  4.4,  21.3,  1.9, 2.8),
                ("Cena",          "Ensalada con palta",            200, "g",  120,  2.0,   8.0,  8.5, 5.0),
                ("Cena",          "Aceite de oliva",                 5, "ml",  45,  0.0,   0.0,  5.0, 0.0),
            ],
        },
        {
            "meta": {
                "name": "Pauta deportista 2800 kcal",
                "category": "Deportista",
                "description": "Alimentación de alto rendimiento para deportistas. Alta en carbohidratos complejos y proteínas. Incluye batido post-entrenamiento.",
                "calories": 2800, "protein_g": 175, "carbs_g": 330, "fat_g": 85,
                "fiber_g": 40, "goal": "Ganancia muscular", "is_predefined": 1,
            },
            "items": [
                ("Desayuno",      "Avena en hojuelas",              80, "g",  304, 10.0,  54.0,  6.0, 8.0),
                ("Desayuno",      "Leche entera",                  300, "ml", 183,  9.9,  14.4,  9.9, 0.0),
                ("Desayuno",      "Huevos revueltos",              120, "g",  172, 12.0,   1.0, 12.8, 0.0),
                ("Desayuno",      "Plátano",                       120, "g",  107,  1.3,  27.0,  0.4, 3.1),
                ("Desayuno",      "Pan integral",                   60, "g",  150,  6.0,  28.0,  1.5, 4.0),
                ("Media mañana",  "Batido de proteínas (whey)",     35, "g",  140, 29.0,   6.0,  2.0, 0.0),
                ("Media mañana",  "Leche semidescremada",          300, "ml", 132, 10.8,  14.4,  3.6, 0.0),
                ("Media mañana",  "Plátano",                       120, "g",  107,  1.3,  27.0,  0.4, 3.1),
                ("Almuerzo",      "Pechuga de pollo a la plancha", 220, "g",  242, 45.0,   0.0,  5.3, 0.0),
                ("Almuerzo",      "Arroz blanco cocido",           200, "g",  260,  5.4,  57.0,  0.6, 0.6),
                ("Almuerzo",      "Porotos cocidos",               100, "g",  127,  8.7,  22.8,  0.5, 6.4),
                ("Almuerzo",      "Ensalada mixta",                200, "g",   40,  2.0,   7.0,  0.5, 3.0),
                ("Almuerzo",      "Aceite de oliva",                10, "ml",  90,  0.0,   0.0, 10.0, 0.0),
                ("Merienda",      "Arroz con leche",               200, "g",  200,  5.4,  38.0,  3.6, 0.2),
                ("Merienda",      "Nueces",                         30, "g",  196,  4.5,   8.0, 17.5, 2.0),
                ("Merienda",      "Manzana",                       150, "g",   78,  0.4,  20.0,  0.3, 3.8),
                ("Cena",          "Salmón a la plancha",           180, "g",  280, 30.0,   0.0, 17.0, 0.0),
                ("Cena",          "Pasta integral cocida",         180, "g",  222,  8.7,  45.0,  1.4, 6.0),
                ("Cena",          "Brócoli al vapor",              150, "g",   51,  4.0,  10.0,  0.5, 3.8),
                ("Cena",          "Aceite de oliva",                10, "ml",  90,  0.0,   0.0, 10.0, 0.0),
                ("Colación",      "Yogur griego natural",          200, "g",  173, 14.7,  10.7,  6.7, 0.0),
                ("Colación",      "Fresas",                        100, "g",   32,  0.7,   7.7,  0.3, 2.0),
            ],
        },
    ]

    for tpl in _PREDEFINED:
        meta = tpl["meta"]
        tid = insert_template(meta)
        for item in tpl["items"]:
            meal_type, food_name, qty, unit, kcal, prot, carbs, fat, fiber = item
            insert_template_item({
                "template_id": tid, "meal_type": meal_type,
                "food_name": food_name, "quantity": qty, "unit": unit,
                "calories": kcal, "protein_g": prot,
                "carbs_g": carbs, "fat_g": fat, "fiber_g": fiber,
            })
