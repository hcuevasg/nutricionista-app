# 🚀 NutriApp Web - Startup Guide

## Estado Actual
- ✅ **FASE 0:** Infrastructure boilerplate completada
- ✅ **FASE 1:** Backend FastAPI core completado (auth, patients CRUD)
- ✅ **FASE 2:** Frontend React pages y layout completados
- 🔄 **FASE 3:** Database migration (pendiente)

## 🎯 MVP Actual - Lo que Funciona

### Backend FastAPI
✅ Registrarse como nutricionista
✅ Login con JWT
✅ Ver usuario actual
✅ CRUD completo de pacientes (create, read, update, delete)
✅ Autenticación multi-tenant (cada usuario solo ve sus datos)

### Frontend React
✅ Login page con validación
✅ Register page
✅ Dashboard (placeholder)
✅ Patients list y detail pages
✅ ISAK form (estructura)
✅ Config page
✅ Responsive design con Stitch colors
✅ Protected routes

---

## 🏃 SETUP RÁPIDO (5 minutos)

### Backend

```bash
# 1. Ir a backend
cd backend

# 2. Crear venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar backend
python main.py
# o
uvicorn main:app --reload

# Servidor disponible en: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### Frontend

```bash
# En otra terminal

# 1. Ir a frontend
cd frontend

# 2. Instalar dependencias
npm install

# 3. Ejecutar dev server
npm run dev

# Acceder en: http://localhost:5173
```

---

## 🧪 PRUEBAS RÁPIDAS

### 1. Registrarse
```
Go to: http://localhost:5173
- Click "Registrate aquí"
- Username: nutricionista1
- Email: nutricionista1@example.com
- Password: password123
```

### 2. Login
```
- Username: nutricionista1
- Password: password123
```

### 3. Crear Paciente
```
POST http://localhost:8000/patients

Headers:
Authorization: Bearer {token_from_login}
Content-Type: application/json

Body:
{
  "name": "Juan Pérez",
  "sex": "M",
  "height_cm": 175,
  "weight_kg": 85,
  "age": 35,
  "phone": "+56912345678",
  "email": "juan@example.com"
}
```

### 4. Listar Pacientes
```
GET http://localhost:8000/patients

Headers:
Authorization: Bearer {token_from_login}
```

---

## 📁 Estructura

```
nutricionista-app/
├── backend/                 # FastAPI
│   ├── main.py             # Punto de entrada
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── auth.py             # Autenticación JWT
│   ├── database.py         # DB config
│   ├── routers/            # Endpoints
│   │   ├── auth.py
│   │   ├── patients.py
│   │   └── ...
│   └── requirements.txt
│
├── frontend/               # React + Vite
│   ├── src/
│   │   ├── pages/          # Pages
│   │   ├── components/     # Reusable components
│   │   ├── context/        # Auth context
│   │   ├── App.tsx         # Main app
│   │   └── main.tsx        # Entry
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
└── STARTUP.md (este archivo)
```

---

## 🔧 Environment Variables

### Backend (.env o .env file)
```
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
DEBUG=True
```

### Frontend (.env.local)
```
VITE_API_URL=http://localhost:8000
```

---

## 📝 API Endpoints Disponibles

```
POST   /auth/register       # Registrarse
POST   /auth/login          # Login
GET    /auth/me             # Usuario actual

GET    /patients            # Listar pacientes del usuario
POST   /patients            # Crear paciente
GET    /patients/{id}       # Ver detalle paciente
PUT    /patients/{id}       # Editar paciente
DELETE /patients/{id}       # Borrar paciente
```

**Nota:** Todos los endpoints excepto `/auth/register` y `/auth/login` requieren header:
```
Authorization: Bearer {token}
```

---

## 🐛 Troubleshooting

### Backend no inicia
```bash
# Verificar Python version
python --version  # Debe ser 3.10+

# Limpiar cache
rm -rf backend/__pycache__
rm backend/test.db

# Reinstalar
pip install -r requirements.txt --force-reinstall
```

### Frontend no carga
```bash
# Limpiar node_modules
rm -rf frontend/node_modules
npm install

# Limpiar cache Vite
rm -rf frontend/.vite
```

### CORS errors
- Verificar que backend corre en http://localhost:8000
- Verificar que frontend corre en http://localhost:5173
- Revisar CORS config en `backend/main.py`

---

## 📊 Próximos Pasos (Roadmap)

### FASE 3: Database Migration (SQLite → PostgreSQL)
- [ ] Crear cuenta Railway.app
- [ ] Crear PostgreSQL en Railway
- [ ] Script de migración
- [ ] Actualizar .env con URL de Railway

### FASE 4: Más Routers
- [ ] Routers de anthropometrics
- [ ] Routers de meal_plans
- [ ] Routers de PDF generation

### FASE 5: Deploy
- [ ] Push a GitHub
- [ ] Deploy backend a Railway
- [ ] Deploy frontend a Vercel
- [ ] Configurar HTTPS y dominio

### FASE 6: Features Adicionales
- [ ] Dashboard con estadísticas reales
- [ ] Gráficos de evolución ISAK
- [ ] Generador de pautas (sin IA inicialmente)
- [ ] PDF export
- [ ] Backups a Google Drive

---

## 💡 Notas Importantes

1. **JWT Token:** Valido por 7 días (configurable en .env)
2. **BD Local:** Usa SQLite (test.db) - cambiar a PostgreSQL en FASE 3
3. **Sin IA:** MVP usa templates editables - agregar IA después
4. **Multi-tenant:** Cada nutricionista solo ve sus datos

---

## ✅ Checklist para MVP

- [x] Login/Register funcional
- [x] CRUD Pacientes
- [x] Autenticación JWT
- [x] Frontend UI completa
- [ ] CRUD ISAK
- [ ] CRUD Meal Plans
- [ ] CRUD Pautas
- [ ] PDF generation
- [ ] DB PostgreSQL online
- [ ] Deploy Railway + Vercel

---

**Última actualización:** 2026-03-13
**Tiempo de desarrollo:** ~6 horas
**Estado:** MVP funcional en local, listo para testing
