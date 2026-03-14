"""Run DB migrations for schema changes."""
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE patients ALTER COLUMN sex TYPE VARCHAR(20)"))
    conn.commit()
    print("✅ Migration complete: sex column expanded to VARCHAR(20)")
