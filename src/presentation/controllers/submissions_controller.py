"""
Controlador de submissions (envíos de soluciones).
Maneja las peticiones HTTP relacionadas con el envío y consulta de soluciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from application.dtos.submission_dto import (
    SubmitSolutionRequest, 
    SubmissionResponse,
    TestCaseResultResponse
)
from application.use_cases.submissions.submit_solution_use_case import SubmitSolutionUseCase
from infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from infrastructure.repositories.submission_repository_impl import SubmissionRepositoryImpl
from infrastructure.services.queue_adapter import QueueAdapter
from infrastructure.persistence.database import get_db
from domain.entities.user import UserRole
from domain.entities.submission import SubmissionStatus
from presentation.middleware.auth_middleware import get_current_user
from workers.redis_queue_service import RedisQueueService

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/submissions", 
    tags=["submissions"],
    responses={404: {"description": "Not found"}}
)


def _build_use_case(db: Session) -> SubmitSolutionUseCase:
    """Factory para crear el caso de uso con sus dependencias."""
    challenge_repository = ChallengeRepositoryImpl(db)
    submission_repository = SubmissionRepositoryImpl(db)
    redis_queue = RedisQueueService()
    queue_adapter = QueueAdapter(redis_queue)
    
    return SubmitSolutionUseCase(
        challenge_repository, 
        submission_repository, 
        queue_adapter
    )


def _get_queue_service() -> RedisQueueService:
    """Factory para obtener el servicio de colas Redis."""
    return RedisQueueService()


def _map_to_response(submission) -> SubmissionResponse:
    """Convierte una entidad Submission a DTO de respuesta."""
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


@router.post(
    "/submit", 
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar solución a un challenge"
)
async def submit_solution(
    submission_request: SubmitSolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Envía una solución de código para un challenge específico.
    
    - **challenge_id**: ID del challenge a resolver
    - **language**: Lenguaje de programación usado
    - **code**: Código fuente de la solución
    """
    logger.info(
        f"[SUBMISSION_REQUEST] User {current_user['email']} ({current_user['id']}) "
        f"submitting solution for challenge {submission_request.challenge_id} "
        f"in {submission_request.language.value}"
    )
    
    try:
        use_case = _build_use_case(db)
        
        submission = await use_case.execute(
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"]),
            challenge_id=submission_request.challenge_id,
            language=submission_request.language,
            code=submission_request.code
        )
        
        logger.info(
            f"[SUBMISSION_CREATED] Submission {submission.id} created successfully "
            f"for user {current_user['id']}, status: {submission.status.value}"
        )
        
        return _map_to_response(submission)
        
    except ValueError as e:
        logger.warning(
            f"[SUBMISSION_VALIDATION_ERROR] User {current_user['id']}, "
            f"Challenge {submission_request.challenge_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"[SUBMISSION_ERROR] User {current_user['id']}, "
            f"Challenge {submission_request.challenge_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/queue/status",
    summary="Get queue status for all languages"
)
async def get_queue_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current state of all submission queues.
    
    Returns the number of pending submissions for each programming language.
    Useful for monitoring system load and queue health.
    
    Requires authentication.
    """
    try:
        queue_service = _get_queue_service()
        
        # Verificar conexión con Redis
        if not queue_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Queue service is unavailable"
            )
        
        # Obtener longitud de todas las colas
        queue_lengths = await queue_service.get_all_queue_lengths()
        
        # Calcular total
        total_pending = sum(queue_lengths.values())
        
        return {
            "status": "healthy",
            "queues": queue_lengths,
            "total_pending": total_pending,
            "service": "redis",
            "available_languages": ["python", "java", "nodejs", "cpp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving queue status: {str(e)}"
        )


@router.get(
    "/queue/{language}",
    summary="Get queue status for a specific language"
)
async def get_language_queue_status(
    language: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current state of a specific language queue.
    
    - **language**: Programming language (python, java, nodejs, cpp)
    
    Returns the number of pending submissions for the specified language.
    
    Requires authentication.
    """
    # Validar lenguaje
    valid_languages = ["python", "java", "nodejs", "cpp"]
    if language.lower() not in valid_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
        )
    
    try:
        queue_service = _get_queue_service()
        
        # Verificar conexión con Redis
        if not queue_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Queue service is unavailable"
            )
        
        # Obtener longitud de la cola específica
        queue_length = await queue_service.get_queue_length(language)
        
        return {
            "language": language,
            "pending_submissions": queue_length,
            "status": "healthy"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking {language} queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving {language} queue status: {str(e)}"
        )


@router.get(
    "/queue/submissions/all",
    summary="View submissions currently in all queues"
)
async def view_queued_submissions(
    limit: int = Query(10, ge=1, le=100, description="Max submissions per queue"),
    current_user: dict = Depends(get_current_user)
):
    """
    View the actual submissions currently waiting in all language queues.
    
    - **limit**: Maximum number of submissions to show per queue (1-100)
    
    Returns detailed information about queued submissions including:
    - Submission ID
    - Challenge ID
    - User ID
    - Language
    - Enqueued timestamp
    - Number of test cases
    
    Useful for monitoring, debugging, and queue management.
    
    Requires authentication. Only ADMIN and PROFESSOR users can view queue contents.
    """
    # Verificar permisos - solo admin y profesor
    user_role = UserRole(current_user["role"])
    if user_role not in [UserRole.ADMIN, UserRole.PROFESSOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and professors can view queue contents"
        )
    
    try:
        queue_service = _get_queue_service()
        
        # Verificar conexión con Redis
        if not queue_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Queue service is unavailable"
            )
        
        # Obtener submissions de todas las colas
        all_queues = await queue_service.peek_all_queues(limit_per_queue=limit)
        
        # Calcular totales
        total_submissions = sum(len(submissions) for submissions in all_queues.values())
        
        # Formatear respuesta con información resumida
        formatted_queues = {}
        for language, submissions in all_queues.items():
            formatted_queues[language] = {
                "count": len(submissions),
                "submissions": [
                    {
                        "submission_id": sub.get("submission_id"),
                        "challenge_id": sub.get("challenge_id"),
                        "user_id": sub.get("user_id"),
                        "language": sub.get("language"),
                        "enqueued_at": sub.get("enqueued_at"),
                        "status": sub.get("status"),
                        "test_cases_count": len(sub.get("test_cases", []))
                    }
                    for sub in submissions
                ]
            }
        
        return {
            "total_submissions": total_submissions,
            "limit_per_queue": limit,
            "queues": formatted_queues,
            "languages": ["python", "java", "nodejs", "cpp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error viewing queued submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving queued submissions: {str(e)}"
        )


@router.get(
    "/queue/{language}/submissions",
    summary="View submissions in a specific language queue"
)
async def view_language_queue_submissions(
    language: str,
    limit: int = Query(20, ge=1, le=100, description="Max submissions to return"),
    current_user: dict = Depends(get_current_user)
):
    """
    View submissions currently waiting in a specific language queue.
    
    - **language**: Programming language (python, java, nodejs, cpp)
    - **limit**: Maximum number of submissions to return (1-100)
    
    Returns detailed information about each queued submission.
    
    Requires authentication. Only ADMIN and PROFESSOR users can view queue contents.
    """
    # Validar lenguaje
    valid_languages = ["python", "java", "nodejs", "cpp"]
    if language.lower() not in valid_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
        )
    
    # Verificar permisos
    user_role = UserRole(current_user["role"])
    if user_role not in [UserRole.ADMIN, UserRole.PROFESSOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and professors can view queue contents"
        )
    
    try:
        queue_service = _get_queue_service()
        
        # Verificar conexión con Redis
        if not queue_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Queue service is unavailable"
            )
        
        # Obtener submissions de la cola específica
        submissions = await queue_service.peek_queue(language, 0, limit - 1)
        
        # Formatear respuesta
        formatted_submissions = [
            {
                "submission_id": sub.get("submission_id"),
                "challenge_id": sub.get("challenge_id"),
                "user_id": sub.get("user_id"),
                "language": sub.get("language"),
                "enqueued_at": sub.get("enqueued_at"),
                "status": sub.get("status"),
                "test_cases_count": len(sub.get("test_cases", [])),
                "code_preview": sub.get("code", "")[:100] + "..." if len(sub.get("code", "")) > 100 else sub.get("code", "")
            }
            for sub in submissions
        ]
        
        # Obtener longitud total de la cola
        total_in_queue = await queue_service.get_queue_length(language)
        
        return {
            "language": language,
            "showing": len(formatted_submissions),
            "total_in_queue": total_in_queue,
            "has_more": total_in_queue > len(formatted_submissions),
            "submissions": formatted_submissions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error viewing {language} queue submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving {language} queue submissions: {str(e)}"
        )


@router.post(
    "/{submission_id}/enqueue",
    summary="Enqueue or re-enqueue a submission for processing"
)
async def enqueue_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually enqueue or re-enqueue an existing submission to Redis for processing.
    
    - **submission_id**: ID of the submission to enqueue
    
    This is useful for:
    - Retrying failed submissions
    - Re-processing submissions with updated test cases
    - Manual intervention by admins/professors
    
    Requires authentication. Only ADMIN, PROFESSOR, or the submission owner can enqueue.
    """
    try:
        submission_repository = SubmissionRepositoryImpl(db)
        challenge_repository = ChallengeRepositoryImpl(db)
        
        # Get the submission
        submission = await submission_repository.find_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Check permissions: owner, admin, or professor
        user_role = UserRole(current_user["role"])
        if (submission.user_id != current_user["id"] and 
            user_role not in [UserRole.ADMIN, UserRole.PROFESSOR]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to enqueue this submission"
            )
        
        # Get challenge and test cases
        challenge = await challenge_repository.find_by_id(submission.challenge_id)
        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found for this submission"
            )
        
        test_cases = await challenge_repository.get_test_cases(submission.challenge_id)
        if not test_cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No test cases found for this challenge"
            )
        
        # Prepare test cases data
        test_cases_data = [
            {
                "id": tc.id,
                "input": tc.input,
                "expected_output": tc.expected_output,
                "is_hidden": tc.is_hidden,
                "order_index": tc.order_index
            }
            for tc in test_cases
        ]
        
        # Enqueue to Redis
        redis_queue = RedisQueueService()
        queue_adapter = QueueAdapter(redis_queue)
        
        success = await redis_queue.enqueue_submission(
            submission_id=submission.id,
            challenge_id=submission.challenge_id,
            user_id=submission.user_id,
            language=submission.language.value,
            code=submission.code,
            test_cases=test_cases_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enqueue submission"
            )
        
        # Update submission status to QUEUED
        submission.status = SubmissionStatus.QUEUED
        await submission_repository.update(submission)
        
        # Get queue length
        queue_length = await redis_queue.get_queue_length(submission.language.value)
        
        return {
            "message": "Submission successfully enqueued",
            "submission_id": submission.id,
            "status": "QUEUED",
            "language": submission.language.value,
            "queue_length": queue_length,
            "test_cases_count": len(test_cases)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error enqueuing submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enqueuing submission: {str(e)}"
        )




@router.get(
    "/my",
    response_model=list,
    summary="Get my submissions"
)
async def get_my_submissions(
    challenge_id: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all submissions by the current authenticated user.
    
    Optional filters:
    - **challenge_id**: Filter by specific challenge
    - **status_filter**: Filter by submission status (QUEUED, RUNNING, ACCEPTED, REJECTED, ERROR)
    
    Returns list of submissions for the current user.
    Requires authentication.
    """
    try:
        submission_repository = SubmissionRepositoryImpl(db)
        
        # Get all submissions for current user
        submissions = await submission_repository.find_by_user_id(current_user["id"])
        
        if not submissions:
            return []
        
        # Filter by challenge if specified
        if challenge_id:
            submissions = [s for s in submissions if str(s.challenge_id) == challenge_id]
        
        # Filter by status if specified
        if status_filter:
            submissions = [s for s in submissions if s.status.value == status_filter.upper()]
        
        # Sort by most recent first
        submissions = sorted(submissions, key=lambda x: x.created_at, reverse=True)
        
        return [_map_to_response(s) for s in submissions]
        
    except Exception as e:
        print(f"Error getting my submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving submissions"
        )


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get submission by ID"
)
async def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific submission.
    
    - **submission_id**: ID of the submission to retrieve
    
    Returns the submission details including test results.
    Users can only see their own submissions, unless they are ADMIN or PROFESSOR.
    
    Requires authentication.
    """
    try:
        submission_repository = SubmissionRepositoryImpl(db)
        submission = await submission_repository.find_by_id(submission_id)
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Verificar permisos: solo el dueño o admin/profesor puede ver
        user_role = UserRole(current_user["role"])
        if (submission.user_id != current_user["id"] and 
            user_role not in [UserRole.ADMIN, UserRole.PROFESSOR]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this submission"
            )
        
        return _map_to_response(submission)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving submission"
        )