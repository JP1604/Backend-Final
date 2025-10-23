"""
Punto de entrada principal de la aplicación.
Configura FastAPI, middleware y rutas.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .presentation.controllers import (
    auth_controller, 
    challenges_controller, 
    submissions_controller
)
from .infrastructure.persistence.database import engine
from .infrastructure.persistence.models import Base

# Crear tablas de base de datos si no existen
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="Online Judge API",
    description="Backend para plataforma de evaluación de algoritmos - Sistema tipo HackerRank",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers de controladores
app.include_router(auth_controller.router)
app.include_router(challenges_controller.router)
app.include_router(submissions_controller.router)


@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz - información básica de la API."""
    return {
        "message": "Online Judge API - Semana 2",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint para monitoreo."""
    return {
        "status": "healthy",
        "service": "online-judge-api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
