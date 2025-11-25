"""
Get Exam Use Case
"""
import logging
from typing import Optional

from domain.entities.exam import Exam
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl

logger = logging.getLogger(__name__)


class GetExamUseCase:
    """Use case for retrieving an exam"""
    
    def __init__(self, exam_repository: ExamRepositoryImpl, course_repository: CourseRepositoryImpl):
        self.exam_repository = exam_repository
        self.course_repository = course_repository
    
    async def execute(self, exam_id: str, user_id: str, user_role) -> Optional[Exam]:
        """
        Get an exam by ID
        
        Args:
            exam_id: ID of the exam to retrieve
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Returns:
            Exam entity if found and user has access, None otherwise
        """
        logger.info(f"[GET_EXAM] User {user_id} requesting exam {exam_id}")
        
        exam = await self.exam_repository.get_exam_by_id(exam_id)
        if not exam:
            logger.warning(f"[EXAM_NOT_FOUND] Exam {exam_id} not found")
            return None
        
        # Check permissions
        course = await self.course_repository.find_by_id(exam.course_id)
        if not course:
            return None
        
        # Students can only see exams in courses they're enrolled in
        if user_role.value == "STUDENT":
            student_courses = await self.course_repository.find_by_student(user_id)
            if exam.course_id not in [c.id for c in student_courses]:
                logger.warning(f"[ACCESS_DENIED] Student {user_id} not enrolled in course {exam.course_id}")
                return None
        
        return exam

