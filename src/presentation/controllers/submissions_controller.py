from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...application.dtos.submission_dto import (
    SubmitSolutionRequest, 
    SubmissionResponse,
    TestCaseResultResponse
)
from ...application.use_cases.submissions.submit_solution_use_case import SubmitSolutionUseCase
from ...infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from ...infrastructure.repositories.submission_repository_impl import SubmissionRepositoryImpl
from ...infrastructure.services.job_queue_service import JobQueueService
from ...infrastructure.persistence.database import get_db
from ...domain.entities.user import UserRole
from ..middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionResponse)
async def submit_solution(
    submission_request: SubmitSolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        challenge_repository = ChallengeRepositoryImpl(db)
        submission_repository = SubmissionRepositoryImpl(db)
        job_queue_service = JobQueueService()
        
        submit_solution_use_case = SubmitSolutionUseCase(
            challenge_repository, 
            submission_repository, 
            job_queue_service
        )
        
        submission = await submit_solution_use_case.execute(
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"]),
            challenge_id=submission_request.challenge_id,
            language=submission_request.language,
            code=submission_request.code
        )
        
        return SubmissionResponse(
            id=submission.id,
            user_id=submission.user_id,
            challenge_id=submission.challenge_id,
            language=submission.language,
            code=submission.code,
            status=submission.status,
            score=submission.score,
            time_ms_total=submission.time_ms_total,
            cases=[
                TestCaseResultResponse(
                    case_id=case.case_id,
                    status=case.status,
                    time_ms=case.time_ms,
                    memory_mb=case.memory_mb,
                    error_message=case.error_message
                )
                for case in submission.cases
            ],
            created_at=submission.created_at.isoformat(),
            updated_at=submission.updated_at.isoformat()
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