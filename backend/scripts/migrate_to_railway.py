#!/usr/bin/env python3
"""
Migration script: SQLite → PostgreSQL on Railway

Usage:
  python3 scripts/migrate_to_railway.py <postgresql_url>

Example:
  python3 scripts/migrate_to_railway.py postgresql://user:password@host:5432/nutriapp
"""

import sys
import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate(pg_url):
    """Migrate from SQLite to PostgreSQL."""
    
    print("🚀 Database Migration: SQLite → PostgreSQL")
    print("=" * 50)
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect("test.db")
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    try:
        pg_engine = create_engine(pg_url, echo=False)
        pg_engine.connect().close()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Get all tables from SQLite
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(tables)} tables: {', '.join(tables)}\n")
    
    # Create tables in PostgreSQL
    from database import Base
    Base.metadata.create_all(bind=pg_engine)
    print("✅ Created all tables in PostgreSQL\n")
    
    # Import models
    import models
    
    Session = sessionmaker(bind=pg_engine)
    session = Session()
    
    try:
        total_rows = 0
        
        # Migrate each table
        for table_name in tables:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"   {table_name}: 0 rows")
                continue
            
            # Convert table name to model name (e.g., patients → Patient)
            model_name = ''.join(word.capitalize() for word in table_name.rstrip('s').split('_')) + ('s' if not table_name.endswith('s') else '')
            if table_name.endswith('ics'):
                model_name = table_name[:-1].capitalize()  # anthropometrics → Anthropometric
            
            # Try different naming conventions
            model_class = None
            for attr_name in dir(models):
                if attr_name.lower() == table_name.lower().rstrip('s'):
                    model_class = getattr(models, attr_name)
                    break
            
            if not model_class:
                print(f"   ⚠️  {table_name}: Could not find model (skipped)")
                continue
            
            # Insert rows
            for row in rows:
                row_dict = dict(row)
                obj = model_class(**row_dict)
                session.add(obj)
            
            session.commit()
            total_rows += len(rows)
            print(f"   ✅ {table_name}: {len(rows)} rows")
        
        print(f"\n✅ Total rows migrated: {total_rows}")
        print("🎉 Migration completed successfully!\n")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
        sqlite_conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/migrate_to_railway.py <postgresql_url>\n")
        print("Example:")
        print("  python3 scripts/migrate_to_railway.py 'postgresql://user:password@host:5432/nutriapp'\n")
        print("To get your Railway PostgreSQL URL:")
        print("  1. Go to https://railway.app")
        print("  2. Create a new project")
        print("  3. Add PostgreSQL service")
        print("  4. Copy the connection string from the 'Connect' tab")
        sys.exit(1)
    
    pg_url = sys.argv[1]
    success = migrate(pg_url)
    sys.exit(0 if success else 1)
