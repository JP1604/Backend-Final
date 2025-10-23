"""
Controlador de challenges (problemas/retos).
Maneja las peticiones HTTP para crear y consultar challenges.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...application.dtos.challenge_dto import (
    CreateChallengeRequest, 
    ChallengeResponse
)
from ...application.use_cases.challenges.create_challenge_use_case import CreateChallengeUseCase
from ...application.use_cases.challenges.get_challenges_use_case import GetChallengesUseCase
from ...infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from ...infrastructure.persistence.database import get_db
from ...domain.entities.user import UserRole
from ..middleware.auth_middleware import get_current_user

router = APIRouter(
    prefix="/challenges", 
    tags=["challenges"],
    responses={404: {"description": "Not found"}}
)


def _get_challenge_repository(db: Session) -> ChallengeRepositoryImpl:
    """Factory para crear el repositorio de challenges."""
    return ChallengeRepositoryImpl(db)


def _map_challenge_to_response(challenge) -> ChallengeResponse:
    """Convierte una entidad Challenge a DTO de respuesta."""
    return ChallengeResponse(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        difficulty=challenge.difficulty,
        tags=challenge.tags,
        time_limit=challenge.time_limit,
        memory_limit=challenge.memory_limit,
        status=challenge.status,
        created_by=challenge.created_by,
        course_id=challenge.course_id,
        created_at=challenge.created_at.isoformat(),
        updated_at=challenge.updated_at.isoformat()
    )


@router.post(
    "/", 
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo challenge"
)
async def create_challenge(
    challenge_request: CreateChallengeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo challenge (solo profesores/admins).
    
    - **title**: Título del problema
    - **description**: Descripción detallada
    - **difficulty**: Nivel de dificultad
    - **time_limit**: Límite de tiempo en ms
    - **memory_limit**: Límite de memoria en MB
    """
    try:
        repository = _get_challenge_repository(db)
        use_case = CreateChallengeUseCase(repository)
        
        challenge = await use_case.execute(
            title=challenge_request.title,
            description=challenge_request.description,
            difficulty=challenge_request.difficulty,
            tags=challenge_request.tags,
            time_limit=challenge_request.time_limit,
            memory_limit=challenge_request.memory_limit,
            created_by=current_user["id"],
            user_role=UserRole(current_user["role"]),
            course_id=challenge_request.course_id
        )
        
        return _map_challenge_to_response(challenge)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error en create_challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/", 
    response_model=List[ChallengeResponse],
    summary="Obtener lista de challenges"
)
async def get_challenges(
    course_id: Optional[str] = Query(None, description="Filtrar por ID de curso"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    difficulty: Optional[str] = Query(None, description="Filtrar por dificultad"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista de challenges según filtros opcionales.
    
    Los usuarios pueden ver solo los challenges publicados,
    mientras que los profesores pueden ver todos.
    """
    try:
        repository = _get_challenge_repository(db)
        use_case = GetChallengesUseCase(repository)
        
        challenges = await use_case.execute(
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"]),
            course_id=course_id,
            status=status,
            difficulty=difficulty
        )
        
        return [_map_challenge_to_response(challenge) for challenge in challenges]
        
    except Exception as e:
        print(f"Error en get_challenges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )