import sqlite3
import os
from datetime import datetime

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
            fat_g        REAL
        );
    """)

    conn.commit()
    _migrate(conn)
    conn.close()


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
    conn.commit()


# ── Patients ─────────────────────────────────────────────────────────────────

def insert_patient(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patients (name, birth_date, age, sex, height_cm, weight_kg,
                              phone, email, address, occupation, notes)
        VALUES (:name,:birth_date,:age,:sex,:height_cm,:weight_kg,
                :phone,:email,:address,:occupation,:notes)
    """, data)
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def update_patient(pid: int, data: dict):
    data["id"] = pid
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute("""
        UPDATE patients SET name=:name, birth_date=:birth_date, age=:age,
            sex=:sex, height_cm=:height_cm, weight_kg=:weight_kg,
            phone=:phone, email=:email, address=:address,
            occupation=:occupation, notes=:notes, updated_at=:updated_at
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


def get_patient(pid: int) -> dict | None:
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


def delete_anthropometric(aid: int):
    conn = get_connection()
    conn.execute("DELETE FROM anthropometrics WHERE id=?", (aid,))
    conn.commit()
    conn.close()


# ── Meal Plans ────────────────────────────────────────────────────────────────

def insert_meal_plan(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO meal_plans (patient_id, name, date, goal, calories, protein_g, carbs_g, fat_g, notes)
        VALUES (:patient_id,:name,:date,:goal,:calories,:protein_g,:carbs_g,:fat_g,:notes)
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


def get_meal_plan(mid: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM meal_plans WHERE id=?", (mid,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Meal Items ────────────────────────────────────────────────────────────────

def insert_meal_item(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO meal_items (plan_id, meal_type, food_name, quantity, unit,
                                calories, protein_g, carbs_g, fat_g)
        VALUES (:plan_id,:meal_type,:food_name,:quantity,:unit,
                :calories,:protein_g,:carbs_g,:fat_g)
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
