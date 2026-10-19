# Migraciones de esquema (Alembic)

Desde la revisión `0001_baseline`, todo cambio de esquema se hace con Alembic.
El backend ejecuta `alembic upgrade head` al arrancar (`main.py`), así que en
Railway basta con hacer push.

Nueva migración (desde `backend/`, con la base local actualizada):

```bash
venv/bin/alembic revision --autogenerate -m "agrega campo X a pacientes"
```

Revisa el archivo generado en `migrations/versions/` antes de hacer commit:
autogenerate no detecta todo (por ejemplo renombres de columnas).

La lista `migrations` de `main.py` queda solo para bases antiguas creadas antes
de Alembic; no le agregues sentencias nuevas.
