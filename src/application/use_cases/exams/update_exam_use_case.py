"""
Update Exam Use Case
"""
import logging
from datetime import datetime
from typing import Optional

from domain.entities.exam import Exam, ExamStatus
from domain.entities.user import UserRole
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl

logger = logging.getLogger(__name__)


class UpdateExamUseCase:
    """Use case for updating an exam"""
    
    def __init__(self, exam_repository: ExamRepositoryImpl, course_repository: CourseRepositoryImpl):
        self.exam_repository = exam_repository
        self.course_repository = course_repository
    
    async def execute(
        self,
        exam_id: str,
        title: Optional[str],
        description: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        duration_minutes: Optional[int],
        max_attempts: Optional[int],
        passing_score: Optional[int],
        status: Optional[ExamStatus],
        user_id: str,
        user_role: UserRole
    ) -> Exam:
        """
        Update an exam
        
        Args:
            exam_id: ID of the exam to update
            title: New title (optional)
            description: New description (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            duration_minutes: New duration (optional)
            max_attempts: New max attempts (optional)
            passing_score: New passing score (optional)
            status: New status (optional)
            user_id: ID of the user updating the exam
            user_role: Role of the user updating the exam
            
        Returns:
            Updated exam entity
            
        Raises:
            ValueError: If validation fails or insufficient permissions
        """
        logger.info(f"[UPDATE_EXAM] User {user_id} updating exam {exam_id}")
        
        # Get existing exam
        exam = await self.exam_repository.get_exam_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        # Check permissions
        course = await self.course_repository.find_by_id(exam.course_id)
        if not course:
            raise ValueError(f"Course {exam.course_id} not found")
        
        if not exam.can_be_managed_by(user_id, course.teacher_id, user_role):
            raise ValueError("You can only update exams in courses you teach")
        
        # Update fields if provided
        if title is not None:
            if not title.strip():
                raise ValueError("Exam title cannot be empty")
            if len(title) > 255:
                raise ValueError("Exam title must be 255 characters or less")
            exam.title = title.strip()
        
        if description is not None:
            exam.description = description.strip() if description else ""
        
        if start_time is not None:
            exam.start_time = start_time
        
        if end_time is not None:
            exam.end_time = end_time
        
        if duration_minutes is not None:
            if duration_minutes <= 0:
                raise ValueError("Duration must be greater than 0")
            exam.duration_minutes = duration_minutes
        
        if max_attempts is not None:
            if max_attempts < 1:
                raise ValueError("Max attempts must be at least 1")
            exam.max_attempts = max_attempts
        
        if passing_score is not None:
            if passing_score < 0 or passing_score > 100:
                raise ValueError("Passing score must be between 0 and 100")
            exam.passing_score = passing_score
        
        if status is not None:
            exam.status = status
        
        # Validate time constraints if both times are set
        if (start_time is not None or end_time is not None) and exam.start_time and exam.end_time:
            if exam.end_time <= exam.start_time:
                raise ValueError("End time must be after start time")
        
        exam.updated_at = datetime.utcnow()
        
        # Save to repository
        updated_exam = await self.exam_repository.update(exam)
        
        logger.info(f"[EXAM_UPDATED] Exam {exam_id} updated by {user_id}")
        
        return updated_exam

