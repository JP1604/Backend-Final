"""
Courses Controller
Handles HTTP requests for course management, enrollment, and challenge assignments
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from application.dtos.course_dto import (
    CreateCourseRequest,
    UpdateCourseRequest,
    EnrollStudentRequest,
    AssignChallengeRequest,
    CourseResponse,
    CourseWithStatsResponse,
    StudentEnrollmentResponse,
    ChallengeAssignmentResponse,
    ExamResponse,
    StudentDetailResponse,
    ExamScoreResponse
)
from application.use_cases.courses.create_course_use_case import CreateCourseUseCase
from application.use_cases.courses.update_course_use_case import UpdateCourseUseCase
from application.use_cases.courses.enroll_student_use_case import EnrollStudentUseCase
from application.use_cases.courses.assign_challenge_use_case import AssignChallengeUseCase
from application.dtos.challenge_dto import ChallengeResponse
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.persistence.database import get_db
from domain.entities.user import UserRole
from domain.entities.course import CourseStatus
from presentation.middleware.auth_middleware import get_current_user
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}}
)


def _build_course_repository(db: Session) -> CourseRepositoryImpl:
    """Factory for course repository"""
    return CourseRepositoryImpl(db)


def _build_user_repository(db: Session) -> UserRepositoryImpl:
    """Factory for user repository"""
    return UserRepositoryImpl(db)


def _build_challenge_repository(db: Session) -> ChallengeRepositoryImpl:
    """Factory for challenge repository"""
    return ChallengeRepositoryImpl(db)


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course"
)
async def create_course(
    course_request: CreateCourseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new course (Professor/Admin only).
    
    - **name**: Course name (required)
    - **description**: Course description
    - **start_date**: Course start date
    - **end_date**: Course end date
    - **status**: Initial status (default: draft)
    """
    logger.info(
        f"[CREATE_COURSE_REQUEST] User {current_user['email']} creating course: {course_request.name}"
    )
    
    try:
        course_repo = _build_course_repository(db)
        use_case = CreateCourseUseCase(course_repo)
        
        course = await use_case.execute(
            name=course_request.name,
            description=course_request.description,
            teacher_id=current_user["id"],
            user_role=UserRole(current_user["role"]),
            start_date=course_request.start_date,
            end_date=course_request.end_date,
            status=course_request.status
        )
        
        logger.info(f"[COURSE_CREATED] Course {course.id} created by {current_user['id']}")
        
        return CourseResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            teacher_id=course.teacher_id,
            status=course.status,
            start_date=course.start_date,
            end_date=course.end_date,
            created_at=course.created_at,
            updated_at=course.updated_at
        )
        
    except ValueError as e:
        logger.warning(f"[CREATE_COURSE_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[CREATE_COURSE_ERROR] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating course"
        )


@router.get(
    "/",
    response_model=List[CourseWithStatsResponse],
    summary="List all courses"
)
async def list_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    teacher_id: str = Query(None, description="Filter by teacher ID"),
    status_filter: CourseStatus = Query(None, description="Filter by status")
):
    """
    List all courses.
    
    - **Students**: See only courses they're enrolled in
    - **Professors**: See courses they teach (or all with teacher_id filter)
    - **Admins**: See all courses
    """
    logger.info(f"[LIST_COURSES] User {current_user['email']} listing courses")
    
    try:
        course_repo = _build_course_repository(db)
        user_role = UserRole(current_user["role"])
        
        # Determine which courses to show based on role
        if user_role == UserRole.ADMIN:
            if teacher_id:
                courses = await course_repo.find_by_teacher(teacher_id)
            else:
                courses = await course_repo.find_all()
        elif user_role == UserRole.PROFESSOR:
            courses = await course_repo.find_by_teacher(current_user["id"])
        else:  # STUDENT
            courses = await course_repo.find_by_student(current_user["id"])
        
        # Filter by status if provided
        if status_filter:
            courses = [c for c in courses if c.status == status_filter]
        
        # Build responses with stats
        responses = []
        for course in courses:
            students = await course_repo.get_students(course.id)
            challenges = await course_repo.get_challenges(course.id)
            
            responses.append(CourseWithStatsResponse(
                id=course.id,
                name=course.name,
                description=course.description,
                teacher_id=course.teacher_id,
                status=course.status,
                start_date=course.start_date,
                end_date=course.end_date,
                student_count=len(students),
                challenge_count=len(challenges),
                created_at=course.created_at,
                updated_at=course.updated_at
            ))
        
        logger.info(f"[COURSES_LISTED] Returned {len(responses)} courses for user {current_user['id']}")
        return responses
        
    except Exception as e:
        logger.error(f"[LIST_COURSES_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing courses"
        )


@router.get(
    "/{course_id}",
    response_model=CourseWithStatsResponse,
    summary="Get course details"
)
async def get_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific course."""
    logger.info(f"[GET_COURSE] User {current_user['email']} requesting course {course_id}")
    
    try:
        course_repo = _build_course_repository(db)
        course = await course_repo.find_by_id(course_id)
        
        if not course:
            logger.warning(f"[COURSE_NOT_FOUND] Course {course_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Check permissions: students can only see courses they're enrolled in
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            student_courses = await course_repo.find_by_student(current_user["id"])
            if course.id not in [c.id for c in student_courses]:
                logger.warning(
                    f"[ACCESS_DENIED] Student {current_user['id']} not enrolled in {course_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not enrolled in this course"
                )
        
        # Get stats
        students = await course_repo.get_students(course.id)
        challenges = await course_repo.get_challenges(course.id)
        
        return CourseWithStatsResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            teacher_id=course.teacher_id,
            status=course.status,
            start_date=course.start_date,
            end_date=course.end_date,
            student_count=len(students),
            challenge_count=len(challenges),
            created_at=course.created_at,
            updated_at=course.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_COURSE_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving course"
        )


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update a course"
)
async def update_course(
    course_id: str,
    course_request: UpdateCourseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing course (Course teacher/Admin only).
    
    - **name**: Course name (optional)
    - **description**: Course description (optional)
    - **start_date**: Course start date (optional)
    - **end_date**: Course end date (optional)
    - **status**: Course status (optional)
    """
    logger.info(
        f"[UPDATE_COURSE_REQUEST] User {current_user['email']} updating course: {course_id}"
    )
    
    try:
        course_repo = _build_course_repository(db)
        use_case = UpdateCourseUseCase(course_repo)
        
        course = await use_case.execute(
            course_id=course_id,
            name=course_request.name,
            description=course_request.description,
            start_date=course_request.start_date,
            end_date=course_request.end_date,
            status=course_request.status,
            requester_id=current_user["id"],
            requester_role=UserRole(current_user["role"])
        )
        
        logger.info(f"[COURSE_UPDATED] Course {course.id} updated by {current_user['id']}")
        
        return CourseResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            teacher_id=course.teacher_id,
            status=course.status,
            start_date=course.start_date,
            end_date=course.end_date,
            created_at=course.created_at,
            updated_at=course.updated_at
        )
        
    except ValueError as e:
        logger.warning(f"[UPDATE_COURSE_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[UPDATE_COURSE_ERROR] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating course"
        )


@router.post(
    "/{course_id}/students",
    response_model=StudentEnrollmentResponse,
    summary="Enroll a student in a course"
)
async def enroll_student(
    course_id: str,
    enrollment_request: EnrollStudentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Enroll a student in a course (Professor/Admin only).
    
    - **student_id**: ID of the student to enroll
    """
    logger.info(
        f"[ENROLL_REQUEST] User {current_user['email']} enrolling "
        f"student {enrollment_request.student_id} in course {course_id}"
    )
    
    try:
        course_repo = _build_course_repository(db)
        user_repo = _build_user_repository(db)
        use_case = EnrollStudentUseCase(course_repo, user_repo)
        
        result = await use_case.execute(
            course_id=course_id,
            student_id=enrollment_request.student_id,
            requester_id=current_user["id"],
            requester_role=UserRole(current_user["role"])
        )
        
        return StudentEnrollmentResponse(
            course_id=course_id,
            student_id=enrollment_request.student_id,
            enrolled_at=datetime.utcnow(),
            success=result,
            message="Student enrolled successfully" if result else "Student already enrolled"
        )
        
    except ValueError as e:
        logger.warning(f"[ENROLL_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[ENROLL_ERROR] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error enrolling student"
        )


@router.post(
    "/{course_id}/challenges",
    response_model=ChallengeAssignmentResponse,
    summary="Assign a challenge to a course"
)
async def assign_challenge(
    course_id: str,
    assignment_request: AssignChallengeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a challenge to a course (Professor/Admin only).
    
    - **challenge_id**: ID of the challenge to assign
    - **order_index**: Display order of the challenge in the course
    """
    logger.info(
        f"[ASSIGN_REQUEST] User {current_user['email']} assigning "
        f"challenge {assignment_request.challenge_id} to course {course_id}"
    )
    
    try:
        course_repo = _build_course_repository(db)
        challenge_repo = _build_challenge_repository(db)
        use_case = AssignChallengeUseCase(course_repo, challenge_repo)
        
        result = await use_case.execute(
            course_id=course_id,
            challenge_id=assignment_request.challenge_id,
            order_index=assignment_request.order_index,
            requester_id=current_user["id"],
            requester_role=UserRole(current_user["role"])
        )
        
        return ChallengeAssignmentResponse(
            course_id=course_id,
            challenge_id=assignment_request.challenge_id,
            assigned_at=datetime.utcnow(),
            order_index=assignment_request.order_index,
            success=result,
            message="Challenge assigned successfully" if result else "Challenge already assigned"
        )
        
    except ValueError as e:
        logger.warning(f"[ASSIGN_ERROR] Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[ASSIGN_ERROR] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error assigning challenge"
        )


@router.get(
    "/{course_id}/students",
    response_model=List[StudentDetailResponse],
    summary="List students enrolled in a course (Teacher/Admin only)"
)
async def list_course_students(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed list of students enrolled in a course.
    
    - **Teachers**: Can only view students in their own courses
    - **Admins**: Can view students in any course
    - **Students**: Not allowed
    """
    logger.info(f"[LIST_STUDENTS] User {current_user['email']} listing students in course {course_id}")
    
    try:
        course_repo = _build_course_repository(db)
        user_repo = _build_user_repository(db)
        course = await course_repo.find_by_id(course_id)
        
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: only course teacher or admin
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot view course student lists"
            )
        
        if not course.can_be_managed_by(current_user["id"], user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view course students"
            )
        
        # Get student IDs
        student_ids = await course_repo.get_students(course_id)
        
        # Get full student details
        student_details = []
        for student_id in student_ids:
            student = await user_repo.find_by_id(student_id)
            if student:
                # Get enrollment date from course_students table
                from infrastructure.persistence.models import course_students
                from sqlalchemy import select
                enrollment = db.execute(
                    select(course_students.c.enrolled_at).where(
                        course_students.c.course_id == course_id,
                        course_students.c.user_id == student_id
                    )
                ).first()
                
                student_details.append(StudentDetailResponse(
                    id=student.id,
                    email=student.email,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    role=student.role.value,
                    enrolled_at=enrollment[0] if enrollment else None
                ))
        
        logger.info(f"[STUDENTS_LISTED] Returned {len(student_details)} students for course {course_id}")
        return student_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LIST_STUDENTS_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing students"
        )


@router.get(
    "/{course_id}/challenges",
    response_model=List[ChallengeResponse],
    summary="List challenges assigned to a course"
)
async def list_course_challenges(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of challenges assigned to a course."""
    from application.dtos.challenge_dto import ChallengeResponse
    from presentation.controllers.challenges_controller import _map_challenge_to_response
    
    logger.info(f"[LIST_CHALLENGES] User {current_user['email']} listing challenges in course {course_id}")
    
    try:
        course_repo = _build_course_repository(db)
        challenge_repo = _build_challenge_repository(db)
        course = await course_repo.find_by_id(course_id)
        
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Students can only see challenges in courses they're enrolled in
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            student_courses = await course_repo.find_by_student(current_user["id"])
            if course.id not in [c.id for c in student_courses]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not enrolled in this course"
                )
        
        # Get challenge IDs assigned to course from course_challenges table
        challenge_ids = await course_repo.get_challenges(course_id)
        
        logger.debug(f"[LIST_CHALLENGES] Found {len(challenge_ids)} challenge IDs assigned to course {course_id}")
        
        # Get full challenge objects
        challenges = []
        for challenge_id in challenge_ids:
            try:
                challenge = await challenge_repo.find_by_id(challenge_id)
                if challenge:
                    # Check if user can view this challenge
                    if challenge.can_be_viewed_by(user_role):
                        challenges.append(challenge)
                    else:
                        logger.debug(f"[LIST_CHALLENGES] Challenge {challenge_id} filtered out (permission check)")
                else:
                    logger.warning(f"[LIST_CHALLENGES] Challenge {challenge_id} not found in repository")
            except Exception as e:
                logger.warning(f"[LIST_CHALLENGES] Error loading challenge {challenge_id}: {str(e)}")
                continue
        
        logger.info(f"[CHALLENGES_LISTED] Returned {len(challenges)} challenges for course {course_id}")
        
        # Map to response format
        from presentation.controllers.challenges_controller import _map_challenge_to_response
        return [_map_challenge_to_response(c) for c in challenges]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LIST_CHALLENGES_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing challenges"
        )


@router.get(
    "/{course_id}/exams",
    response_model=List[ExamResponse],
    summary="List exams in a course (Teacher/Admin only)"
)
async def list_course_exams(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of all exams in a course.
    
    - **Teachers**: Can only view exams in their own courses
    - **Admins**: Can view exams in any course
    - **Students**: Not allowed
    """
    logger.info(f"[LIST_EXAMS] User {current_user['email']} listing exams in course {course_id}")
    
    try:
        course_repo = _build_course_repository(db)
        exam_repo = ExamRepositoryImpl(db)
        course = await course_repo.find_by_id(course_id)
        
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: only course teacher or admin
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot view course exams"
            )
        
        if not course.can_be_managed_by(current_user["id"], user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view course exams"
            )
        
        # Get exams for this course
        exams_data = await exam_repo.get_exams_by_course_id(course_id)
        
        exams = []
        for exam_data in exams_data:
            exams.append(ExamResponse(
                id=exam_data["id"],
                course_id=exam_data["course_id"],
                title=exam_data["title"],
                description=exam_data.get("description"),
                start_time=exam_data["start_time"],
                end_time=exam_data["end_time"],
                duration_minutes=exam_data["duration_minutes"],
                max_attempts=exam_data["max_attempts"],
                passing_score=exam_data.get("passing_score"),
                status=exam_data["status"],
                created_at=exam_data["created_at"],
                updated_at=exam_data["updated_at"]
            ))
        
        logger.info(f"[EXAMS_LISTED] Returned {len(exams)} exams for course {course_id}")
        return exams
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LIST_EXAMS_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing exams"
        )


@router.get(
    "/{course_id}/exam-scores",
    response_model=List[ExamScoreResponse],
    summary="Get exam scores for all students (Teacher/Admin only)"
)
async def get_course_exam_scores(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all exam scores for all students in a course.
    
    Returns a comprehensive list of all exam attempts with scores,
    allowing teachers to see overall student performance.
    
    - **Teachers**: Can only view scores in their own courses
    - **Admins**: Can view scores in any course
    - **Students**: Not allowed
    """
    logger.info(f"[GET_EXAM_SCORES] User {current_user['email']} getting exam scores for course {course_id}")
    
    try:
        course_repo = _build_course_repository(db)
        exam_repo = ExamRepositoryImpl(db)
        course = await course_repo.find_by_id(course_id)
        
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: only course teacher or admin
        user_role = UserRole(current_user["role"])
        if user_role == UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot view exam scores"
            )
        
        if not course.can_be_managed_by(current_user["id"], user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view exam scores"
            )
        
        # Get all exam scores for this course
        scores_data = await exam_repo.get_exam_scores_by_course_id(course_id)
        
        scores = []
        for score_data in scores_data:
            scores.append(ExamScoreResponse(
                exam_id=score_data["exam_id"],
                exam_title=score_data["exam_title"],
                user_id=score_data["user_id"],
                attempt_id=score_data["attempt_id"],
                score=score_data["score"],
                passed=score_data["passed"],
                started_at=score_data["started_at"],
                submitted_at=score_data.get("submitted_at"),
                is_active=score_data["is_active"]
            ))
        
        logger.info(f"[EXAM_SCORES_RETRIEVED] Returned {len(scores)} exam scores for course {course_id}")
        return scores
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_EXAM_SCORES_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving exam scores"
        )

