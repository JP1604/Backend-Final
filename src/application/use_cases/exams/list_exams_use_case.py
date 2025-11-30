"""
List Exams Use Case
"""
import logging
from typing import List, Optional

from domain.entities.exam import Exam
from domain.entities.user import UserRole
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl

logger = logging.getLogger(__name__)


class ListExamsUseCase:
    """Use case for listing exams"""
    
    def __init__(self, exam_repository: ExamRepositoryImpl, course_repository: CourseRepositoryImpl):
        self.exam_repository = exam_repository
        self.course_repository = course_repository
    
    async def execute(
        self,
        user_id: str,
        user_role: UserRole,
        course_id: Optional[str] = None
    ) -> List[Exam]:
        """
        List exams based on user role and filters
        
        Args:
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            course_id: Optional course ID to filter by
            
        Returns:
            List of exam entities the user has access to
        """
        logger.info(f"[LIST_EXAMS] User {user_id} (role: {user_role}) listing exams")
        
        if user_role == UserRole.ADMIN:
            # Admins can see all exams
            if course_id:
                exams = await self.exam_repository.find_by_course_id(course_id)
            else:
                exams = await self.exam_repository.find_all()
        elif user_role == UserRole.PROFESSOR:
            # Professors can see exams in courses they teach
            if course_id:
                # Verify they teach this course
                course = await self.course_repository.find_by_id(course_id)
                if course and course.teacher_id == user_id:
                    exams = await self.exam_repository.find_by_course_id(course_id)
                else:
                    exams = []
            else:
                # Get all courses they teach, then get exams for those courses
                courses = await self.course_repository.find_by_teacher(user_id)
                all_exams = []
                for course in courses:
                    course_exams = await self.exam_repository.find_by_course_id(course.id)
                    all_exams.extend(course_exams)
                exams = all_exams
        else:  # STUDENT
            # Students can see exams in courses they're enrolled in
            if course_id:
                # Verify they're enrolled
                student_courses = await self.course_repository.find_by_student(user_id)
                if course_id in [c.id for c in student_courses]:
                    exams = await self.exam_repository.find_by_course_id(course_id)
                else:
                    exams = []
            else:
                # Get all courses they're enrolled in, then get exams
                courses = await self.course_repository.find_by_student(user_id)
                all_exams = []
                for course in courses:
                    course_exams = await self.exam_repository.find_by_course_id(course.id)
                    all_exams.extend(course_exams)
                exams = all_exams
        
        logger.info(f"[EXAMS_LISTED] Returned {len(exams)} exams for user {user_id}")
        return exams

