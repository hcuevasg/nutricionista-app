"""
NutriApp Backend - FastAPI
Multi-tenant nutrition management platform
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import auth, patients

# Import database
from database import engine, Base

# Create tables on startup
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 NutriApp Backend Starting...")
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
    "http://localhost:3000",      # Local React dev
    "http://localhost:5173",      # Vite default
    "https://nutriapp.vercel.app", # Production frontend
    "*"  # Allow all (restrict in production)
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
