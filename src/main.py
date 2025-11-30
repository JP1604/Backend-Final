"""
Punto de entrada principal de la aplicación.
Configura FastAPI, middleware y rutas.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from presentation.controllers import (
    auth_controller, 
    challenges_controller, 
    submissions_controller,
    users_controller,
    courses_controller,
    exams_controller
)
from infrastructure.persistence.database import engine
from infrastructure.persistence.models import Base

# Crear tablas de base de datos si no existen
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="Online Judge API",
    description="Backend para plataforma de evaluación de algoritmos - Sistema tipo HackerRank",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False  # Desactivar redirecciones automáticas de barras finales
)

# Middleware para manejar correctamente las peticiones a través de proxy
@app.middleware("http")
async def proxy_headers_middleware(request: Request, call_next):
    """Middleware para manejar correctamente los headers cuando se está detrás de un proxy."""
    # Asegurar que los headers X-Forwarded-* se pasen correctamente
    response = await call_next(request)
    return response

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes en desarrollo
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Registrar routers de controladores
app.include_router(auth_controller.router)
app.include_router(challenges_controller.router)
app.include_router(submissions_controller.router)
app.include_router(users_controller.router)
app.include_router(courses_controller.router)
app.include_router(exams_controller.router)


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
