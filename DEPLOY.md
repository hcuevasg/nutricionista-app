# 🚀 Deployment Guide - NutriApp Web

## Prerequisites
- Railway.app account (free tier available)
- Vercel account (free tier available)
- Git repository pushed to GitHub

---

## FASE 5: Database Migration & Railway Setup

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Click "Provision PostgreSQL"
4. Wait for database to be ready

### Step 2: Get PostgreSQL Connection URL

In Railway dashboard:
1. Go to your PostgreSQL service
2. Click "Connect"
3. Copy the full connection string:
   ```
   postgresql://user:password@host.railway.internal:5432/railway
   ```

### Step 3: Run Migration

```bash
cd backend

# Activate venv
source venv/bin/activate

# Run migration script
python3 scripts/migrate_to_railway.py "postgresql://user:password@host:5432/dbname"
```

### Step 4: Update Environment Variables

Update `.env`:
```bash
DATABASE_URL=postgresql://user:password@host:5432/nutriapp
SECRET_KEY=<generate-secure-key>
DEBUG=False
```

Generate secure key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## FASE 6: Deploy Backend to Railway

### Option 1: Manual Deploy (Recommended First Time)

1. **Create `Procfile` in backend/**:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. **In Railway Dashboard**:
   - Click "New Service" → "GitHub Repo"
   - Select nutricionista-app repo
   - Set root directory: `backend/`
   - Add environment variables:
     - `DATABASE_URL`: (from PostgreSQL service)
     - `SECRET_KEY`: (from .env)
     - `ALGORITHM`: HS256
     - `ACCESS_TOKEN_EXPIRE_DAYS`: 7
     - `DEBUG`: False

3. **Deploy**:
   - Railway automatically deploys on push to main
   - Monitor in "Deployments" tab

### Option 2: CLI Deploy

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy backend
cd backend
railway up
```

---

## FASE 6b: Deploy Frontend to Vercel

### Step 1: Connect Frontend to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

### Step 2: Configure Environment Variables

In Vercel dashboard:
1. Go to Settings → Environment Variables
2. Add:
   - `VITE_API_URL`: https://your-railway-backend.railway.app
   - `VITE_ENVIRONMENT`: production

### Step 3: Update Vite Config

Update `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

---

## FASE 7: Final Testing & Polish

### Pre-Deployment Checklist

- [ ] Backend starts without errors
- [ ] Database migration completes
- [ ] All API endpoints respond
- [ ] Frontend builds without errors
- [ ] Frontend connects to backend API
- [ ] Login/register flow works E2E
- [ ] Patient CRUD works
- [ ] Authentication persists on page reload

### Post-Deployment Testing

```bash
# Test backend health
curl https://your-backend.railway.app/health

# Test frontend loads
curl https://your-frontend.vercel.app

# Test API with token
curl -X POST https://your-backend.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass"}'
```

### Optional: Automated Backups

Create `backend/scripts/backup_to_gdrive.py`:
```python
# Backup PostgreSQL to Google Drive
# Run as cron job: 0 2 * * * python3 scripts/backup_to_gdrive.py
```

---

## URLs After Deployment

- **Backend API**: https://your-project.railway.app
- **API Docs**: https://your-project.railway.app/docs
- **Frontend**: https://your-project.vercel.app
- **PostgreSQL**: Managed by Railway

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
railway logs

# Verify dependencies
pip install -r requirements.txt

# Test locally first
python3 main.py
```

### Migration fails
```bash
# Check PostgreSQL connection
psql postgresql://user:pass@host:5432/db

# Verify models match database
python3 -c "from models import *; print('Models loaded')"
```

### Frontend doesn't connect to backend
1. Check `VITE_API_URL` is set correctly
2. Verify CORS in `backend/main.py`
3. Check network requests in browser DevTools

---

## Next Steps

After deployment:
1. Share frontend URL with users
2. Set up monitoring (Railway + Vercel dashboards)
3. Configure backup strategy
4. Plan feature releases
5. Consider auto-scaling if needed

---

**Last updated:** 2026-03-13
**Time to deploy:** ~30 minutes (first time), ~5 minutes (subsequent)
