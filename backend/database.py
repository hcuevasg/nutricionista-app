"""Database configuration and setup."""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from os import getenv
from urllib.parse import urlparse

# Database URL
DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./test.db")

# For PostgreSQL, ensure database exists
if "postgresql" in DATABASE_URL:
    try:
        # Parse the database URL
        parsed = urlparse(DATABASE_URL)
        db_name = parsed.path.lstrip('/')
        admin_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"

        # Connect to postgres database to create our database if needed
        admin_engine = create_engine(admin_url)
        with admin_engine.connect() as conn:
            conn.execute(text("COMMIT"))  # Close any open transaction
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            if not result.fetchone():
                # Database doesn't exist, create it
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✅ Created database: {db_name}")
            conn.commit()
        admin_engine.dispose()
    except Exception as e:
        print(f"⚠️ Could not ensure database exists: {e}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
