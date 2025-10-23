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

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.post("/", response_model=ChallengeResponse)
async def create_challenge(
    challenge_request: CreateChallengeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        challenge_repository = ChallengeRepositoryImpl(db)
        create_challenge_use_case = CreateChallengeUseCase(challenge_repository)
        
        challenge = await create_challenge_use_case.execute(
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
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=List[ChallengeResponse])
async def get_challenges(
    course_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        challenge_repository = ChallengeRepositoryImpl(db)
        get_challenges_use_case = GetChallengesUseCase(challenge_repository)
        
        challenges = await get_challenges_use_case.execute(
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"]),
            course_id=course_id,
            status=status,
            difficulty=difficulty
        )
        
        return [
            ChallengeResponse(
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
            for challenge in challenges
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )