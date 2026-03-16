"""Run DB migrations for schema changes."""
from database import engine
from sqlalchemy import text

migrations = [
    ("clinic_name",    "ALTER TABLE nutritionists ADD COLUMN clinic_name VARCHAR(255)"),
    ("report_tagline", "ALTER TABLE nutritionists ADD COLUMN report_tagline VARCHAR(500)"),
    ("logo_base64",    "ALTER TABLE nutritionists ADD COLUMN logo_base64 TEXT"),
]

with engine.connect() as conn:
    for col, sql in migrations:
        try:
            conn.execute(text(sql))
            conn.commit()
            print(f"✅ Column added: {col}")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"⏭️  Already exists: {col}")
            else:
                raise
