"""
NutriApp Backend - FastAPI
Multi-tenant nutrition management platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import auth, patients, anthropometrics, meal_plans, dashboard

# Import database
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 NutriApp Backend Starting...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")
        # Continue anyway - database might already exist
    yield
    # Shutdown
    print("🛑 NutriApp Backend Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="NutriApp API",
    description="Multi-tenant nutrition management platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", "https://nutricionista-app.vercel.app"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(anthropometrics.router)
app.include_router(meal_plans.router)
app.include_router(dashboard.router)


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "NutriApp Backend v0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
