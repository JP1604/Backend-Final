"""
Create Exam Use Case
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from domain.entities.exam import Exam, ExamStatus
from domain.entities.user import UserRole
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl

logger = logging.getLogger(__name__)


class CreateExamUseCase:
    """Use case for creating a new exam"""
    
    def __init__(self, exam_repository: ExamRepositoryImpl, course_repository: CourseRepositoryImpl):
        self.exam_repository = exam_repository
        self.course_repository = course_repository
    
    async def execute(
        self,
        course_id: str,
        title: str,
        description: Optional[str],
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
        max_attempts: int,
        passing_score: Optional[int],
        status: ExamStatus,
        created_by: str,
        user_role: UserRole
    ) -> Exam:
        """
        Create a new exam
        
        Args:
            course_id: ID of the course this exam belongs to
            title: Exam title
            description: Exam description
            start_time: When the exam becomes available
            end_time: When the exam closes
            duration_minutes: Maximum time per student attempt
            max_attempts: Maximum attempts per student
            passing_score: Minimum score to pass (0-100)
            status: Initial exam status
            created_by: ID of the user creating the exam
            user_role: Role of the user creating the exam
            
        Returns:
            Created exam entity
            
        Raises:
            ValueError: If validation fails or insufficient permissions
        """
        logger.info(f"[CREATE_EXAM] User {created_by} creating exam: {title} for course {course_id}")
        
        # Validate permissions
        if not self._can_create_exam(user_role):
            logger.warning(f"[CREATE_EXAM_DENIED] User {created_by} lacks permission (role: {user_role})")
            raise ValueError("Only professors and administrators can create exams")
        
        # Validate course exists
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Check if user can manage this course
        if not course.can_be_managed_by(created_by, user_role):
            raise ValueError("You can only create exams for courses you teach")
        
        # Validate input
        self._validate_exam_data(title, start_time, end_time, duration_minutes, max_attempts, passing_score)
        
        # Create exam entity
        exam = Exam(
            id=str(uuid.uuid4()),
            course_id=course_id,
            title=title.strip(),
            description=description.strip() if description else "",
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            max_attempts=max_attempts,
            passing_score=passing_score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=created_by
        )
        
        # Save to repository
        created_exam = await self.exam_repository.save(exam)
        
        logger.info(
            f"[EXAM_CREATED] Exam {created_exam.id} '{created_exam.title}' "
            f"created by {created_by} for course {course_id}"
        )
        
        return created_exam
    
    def _can_create_exam(self, user_role: UserRole) -> bool:
        """Check if user can create exams"""
        return user_role in [UserRole.ADMIN, UserRole.PROFESSOR]
    
    def _validate_exam_data(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
        max_attempts: int,
        passing_score: Optional[int]
    ):
        """Validate exam data"""
        if not title or not title.strip():
            raise ValueError("Exam title is required")
        
        if len(title) > 255:
            raise ValueError("Exam title must be 255 characters or less")
        
        if end_time <= start_time:
            raise ValueError("End time must be after start time")
        
        if duration_minutes <= 0:
            raise ValueError("Duration must be greater than 0")
        
        if max_attempts < 1:
            raise ValueError("Max attempts must be at least 1")
        
        if passing_score is not None and (passing_score < 0 or passing_score > 100):
            raise ValueError("Passing score must be between 0 and 100")

