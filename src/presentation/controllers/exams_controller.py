from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from infrastructure.persistence.database import get_db
from presentation.middleware.auth_middleware import get_current_user
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl
from infrastructure.repositories.submission_repository_impl import SubmissionRepositoryImpl
from application.use_cases.exams.start_exam_attempt_use_case import StartExamAttemptUseCase
from application.use_cases.exams.submit_exam_attempt_use_case import SubmitExamAttemptUseCase
from application.use_cases.exams.create_exam_use_case import CreateExamUseCase
from application.use_cases.exams.get_exam_use_case import GetExamUseCase
from application.use_cases.exams.list_exams_use_case import ListExamsUseCase
from application.use_cases.exams.update_exam_use_case import UpdateExamUseCase
from application.dtos.exam_dto import (
    CreateExamRequest,
    UpdateExamRequest,
    ExamResponse,
    ExamAttemptResponse,
    ExamResultsResponse
)
from domain.entities.user import UserRole
from domain.entities.exam import ExamStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/exams",
    tags=["exams"],
    responses={404: {"description": "Not found"}}
)


def _build_exam_repository(db: Session) -> ExamRepositoryImpl:
    """Factory for exam repository"""
    return ExamRepositoryImpl(db)


def _build_course_repository(db: Session) -> CourseRepositoryImpl:
    """Factory for course repository"""
    return CourseRepositoryImpl(db)


@router.post(
    "/",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exam"
)
async def create_exam(
    exam_request: CreateExamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new exam (Professor/Admin only).
    
    - **course_id**: ID of the course this exam belongs to
    - **title**: Exam title (required)
    - **description**: Exam description
    - **start_time**: When the exam becomes available
    - **end_time**: When the exam closes
    - **duration_minutes**: Maximum time per student attempt
    - **max_attempts**: Maximum attempts per student
    - **passing_score**: Minimum score to pass (0-100, optional)
    - **status**: Initial status (default: draft)
    """
    logger.info(
        f"[CREATE_EXAM_REQUEST] User {current_user['email']} creating exam: {exam_request.title}"
    )
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)
        use_case = CreateExamUseCase(exam_repo, course_repo)
        
        exam = await use_case.execute(
            course_id=exam_request.course_id,
            title=exam_request.title,
            description=exam_request.description,
            start_time=exam_request.start_time,
            end_time=exam_request.end_time,
            duration_minutes=exam_request.duration_minutes,
            max_attempts=exam_request.max_attempts,
            passing_score=exam_request.passing_score,
            status=exam_request.status,
            created_by=current_user["id"],
            user_role=UserRole(current_user["role"])
        )
        
        logger.info(f"[EXAM_CREATED] Exam {exam.id} created by {current_user['id']}")
        
        return ExamResponse(
            id=exam.id,
            course_id=exam.course_id,
            title=exam.title,
            description=exam.description,
            status=exam.status,
            start_time=exam.start_time,
            end_time=exam.end_time,
            duration_minutes=exam.duration_minutes,
            max_attempts=exam.max_attempts,
            passing_score=exam.passing_score,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            created_by=exam.created_by
        )
        
    except ValueError as e:
        logger.warning(f"[CREATE_EXAM_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[CREATE_EXAM_ERROR] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating exam"
        )


@router.get(
    "/",
    response_model=List[ExamResponse],
    summary="List exams"
)
async def list_exams(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    course_id: Optional[str] = Query(None, description="Filter by course ID")
):
    """
    List exams based on user role.
    
    - **Students**: See exams in courses they're enrolled in
    - **Professors**: See exams in courses they teach
    - **Admins**: See all exams
    """
    logger.info(f"[LIST_EXAMS] User {current_user['email']} listing exams")
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)
        use_case = ListExamsUseCase(exam_repo, course_repo)
        
        exams = await use_case.execute(
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"]),
            course_id=course_id
        )
        
        responses = []
        for exam in exams:
            responses.append(ExamResponse(
                id=exam.id,
                course_id=exam.course_id,
                title=exam.title,
                description=exam.description,
                status=exam.status,
                start_time=exam.start_time,
                end_time=exam.end_time,
                duration_minutes=exam.duration_minutes,
                max_attempts=exam.max_attempts,
                passing_score=exam.passing_score,
                created_at=exam.created_at,
                updated_at=exam.updated_at,
                created_by=exam.created_by
            ))
        
        logger.info(f"[EXAMS_LISTED] Returned {len(responses)} exams for user {current_user['id']}")
        return responses
        
    except Exception as e:
        logger.error(f"[LIST_EXAMS_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing exams"
        )


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Get exam details"
)
async def get_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific exam."""
    logger.info(f"[GET_EXAM] User {current_user['email']} requesting exam {exam_id}")
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)
        use_case = GetExamUseCase(exam_repo, course_repo)
        
        exam = await use_case.execute(
            exam_id=exam_id,
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"])
        )
        
        if not exam:
            logger.warning(f"[EXAM_NOT_FOUND] Exam {exam_id} not found or access denied")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
        
        return ExamResponse(
            id=exam.id,
            course_id=exam.course_id,
            title=exam.title,
            description=exam.description,
            status=exam.status,
            start_time=exam.start_time,
            end_time=exam.end_time,
            duration_minutes=exam.duration_minutes,
            max_attempts=exam.max_attempts,
            passing_score=exam.passing_score,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            created_by=exam.created_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_EXAM_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving exam"
        )


@router.put(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Update exam"
)
async def update_exam(
    exam_id: str,
    exam_request: UpdateExamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an exam (Professor/Admin only).
    
    Only professors teaching the course or admins can update exams.
    """
    logger.info(f"[UPDATE_EXAM_REQUEST] User {current_user['email']} updating exam {exam_id}")
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)
        use_case = UpdateExamUseCase(exam_repo, course_repo)
        
        exam = await use_case.execute(
            exam_id=exam_id,
            title=exam_request.title,
            description=exam_request.description,
            start_time=exam_request.start_time,
            end_time=exam_request.end_time,
            duration_minutes=exam_request.duration_minutes,
            max_attempts=exam_request.max_attempts,
            passing_score=exam_request.passing_score,
            status=exam_request.status,
            user_id=current_user["id"],
            user_role=UserRole(current_user["role"])
        )
        
        logger.info(f"[EXAM_UPDATED] Exam {exam_id} updated by {current_user['id']}")
        
        return ExamResponse(
            id=exam.id,
            course_id=exam.course_id,
            title=exam.title,
            description=exam.description,
            status=exam.status,
            start_time=exam.start_time,
            end_time=exam.end_time,
            duration_minutes=exam.duration_minutes,
            max_attempts=exam.max_attempts,
            passing_score=exam.passing_score,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            created_by=exam.created_by
        )
        
    except ValueError as e:
        logger.warning(f"[UPDATE_EXAM_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[UPDATE_EXAM_ERROR] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating exam"
        )


@router.get(
    "/{exam_id}/attempts",
    response_model=List[ExamAttemptResponse],
    summary="Get exam attempts (Teacher/Admin only)"
)
async def get_exam_attempts(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all attempts for an exam.
    
    - **Teachers**: Can view attempts for exams in their courses
    - **Admins**: Can view attempts for any exam
    - **Students**: Not allowed
    """
    logger.info(f"[GET_EXAM_ATTEMPTS] User {current_user['email']} getting attempts for exam {exam_id}")
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)
        
        # Check exam exists and permissions
        exam = await exam_repo.get_exam_by_id(exam_id)
        if not exam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
        
        course = await course_repo.find_by_id(exam.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot view exam attempts"
            )
        
        if not exam.can_be_managed_by(current_user["id"], course.teacher_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view exam attempts"
            )
        
        # Get attempts
        attempts_data = await exam_repo.get_attempts_by_exam_id(exam_id)
        
        attempts = []
        for attempt_data in attempts_data:
            attempts.append(ExamAttemptResponse(
                id=attempt_data["id"],
                exam_id=exam_id,
                user_id=attempt_data["user_id"],
                score=attempt_data["score"],
                passed=attempt_data["passed"],
                started_at=attempt_data["started_at"],
                submitted_at=attempt_data.get("submitted_at"),
                is_active=False  # All returned attempts are finalized
            ))
        
        logger.info(f"[ATTEMPTS_RETRIEVED] Returned {len(attempts)} attempts for exam {exam_id}")
        return attempts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_EXAM_ATTEMPTS_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving exam attempts"
        )


@router.get(
    "/{exam_id}/results",
    response_model=ExamResultsResponse,
    summary="Get exam results summary (Teacher/Admin only)"
)
async def get_exam_results(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get exam results summary with statistics.
    
    - **Teachers**: Can view results for exams in their courses
    - **Admins**: Can view results for any exam
    - **Students**: Not allowed
    """
    logger.info(f"[GET_EXAM_RESULTS] User {current_user['email']} getting results for exam {exam_id}")
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)
        
        # Check exam exists and permissions
        exam = await exam_repo.get_exam_by_id(exam_id)
        if not exam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
        
        course = await course_repo.find_by_id(exam.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot view exam results"
            )
        
        if not exam.can_be_managed_by(current_user["id"], course.teacher_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view exam results"
            )
        
        # Get attempts
        attempts_data = await exam_repo.get_attempts_by_exam_id(exam_id)
        
        attempts = []
        total_score = 0
        passed_count = 0
        
        for attempt_data in attempts_data:
            attempts.append(ExamAttemptResponse(
                id=attempt_data["id"],
                exam_id=exam_id,
                user_id=attempt_data["user_id"],
                score=attempt_data["score"],
                passed=attempt_data["passed"],
                started_at=attempt_data["started_at"],
                submitted_at=attempt_data.get("submitted_at"),
                is_active=False
            ))
            total_score += attempt_data["score"]
            if attempt_data["passed"]:
                passed_count += 1
        
        average_score = total_score / len(attempts) if attempts else 0
        
        logger.info(f"[RESULTS_RETRIEVED] Exam {exam_id}: {len(attempts)} attempts, avg score: {average_score:.2f}")
        
        return ExamResultsResponse(
            exam_id=exam_id,
            exam_title=exam.title,
            total_attempts=len(attempts),
            passed_attempts=passed_count,
            average_score=round(average_score, 2),
            attempts=attempts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_EXAM_RESULTS_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving exam results"
        )


@router.post("/{exam_id}/start")
async def start_exam_attempt(exam_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Start an exam attempt for the current user."""
    logger.info(f"[START_EXAM_ATTEMPT] User {current_user['email']} starting attempt for exam {exam_id}")
    
    try:
        exam_repo = _build_exam_repository(db)
        course_repo = _build_course_repository(db)

        uc = StartExamAttemptUseCase(exam_repo, course_repo)
        attempt = await uc.execute(exam_id, current_user['id'])
        
        logger.info(f"[ATTEMPT_STARTED] Attempt {attempt['id']} started for exam {exam_id}")
        return {"attempt_id": attempt['id'], "started_at": attempt['started_at'].isoformat()}

    except ValueError as e:
        logger.warning(f"[START_ATTEMPT_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[START_ATTEMPT_ERROR] Failed to start exam attempt {exam_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start exam attempt")


@router.post("/attempts/{attempt_id}/submit")
async def submit_exam_attempt(attempt_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Submit and finalize an exam attempt."""
    logger.info(f"[SUBMIT_EXAM_ATTEMPT] User {current_user['email']} submitting attempt {attempt_id}")
    
    try:
        exam_repo = _build_exam_repository(db)
        submission_repo = SubmissionRepositoryImpl(db)

        uc = SubmitExamAttemptUseCase(exam_repo, submission_repo, db)
        finalized = await uc.execute(attempt_id)
        
        logger.info(f"[ATTEMPT_SUBMITTED] Attempt {attempt_id} submitted with score {finalized['score']}")
        return {
            "attempt_id": finalized['id'],
            "score": finalized['score'],
            "passed": finalized['passed'],
            "submitted_at": finalized['submitted_at'].isoformat() if finalized.get('submitted_at') else None
        }

    except ValueError as e:
        logger.warning(f"[SUBMIT_ATTEMPT_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[SUBMIT_ATTEMPT_ERROR] Failed to submit exam attempt {attempt_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit exam attempt")