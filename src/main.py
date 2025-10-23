from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .presentation.controllers import auth_controller, challenges_controller, submissions_controller
from .infrastructure.persistence.database import engine
from .infrastructure.persistence.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Online Judge API",
    description="Backend para plataforma de evaluación de algoritmos",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_controller.router)
app.include_router(challenges_controller.router)
app.include_router(submissions_controller.router)


@app.get("/")
async def root():
    return {"message": "Online Judge API - Semana 2"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
