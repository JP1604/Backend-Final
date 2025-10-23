"""
Configuración de la base de datos.
Gestiona la conexión y sesiones de SQLAlchemy.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL desde variables de entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5436/online_judge"
)

# Crear engine de SQLAlchemy
# pool_pre_ping=True verifica conexiones antes de usarlas
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Cambiar a True para ver queries SQL en desarrollo
)

# SessionLocal: factory para crear sesiones de base de datos
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Base: clase base para modelos ORM
Base = declarative_base()


def get_db():
    """
    Dependency para obtener una sesión de base de datos.
    Se usa con FastAPI Depends() para inyectar la sesión en endpoints.
    
    La sesión se cierra automáticamente al finalizar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
