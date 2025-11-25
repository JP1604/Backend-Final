"""
Enroll Student Use Case
"""
import logging
from domain.entities.user import UserRole
from domain.entities.course import CourseStatus
from domain.repositories.course_repository import CourseRepository
from domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class EnrollStudentUseCase:
    """Use case for enrolling a student in a course"""
    
    def __init__(
        self,
        course_repository: CourseRepository,
        user_repository: UserRepository
    ):
        self.course_repository = course_repository
        self.user_repository = user_repository
    
    async def execute(
        self,
        course_id: str,
        student_id: str,
        requester_id: str,
        requester_role: UserRole
    ) -> bool:
        """
        Enroll a student in a course
        
        Args:
            course_id: ID of the course
            student_id: ID of the student to enroll
            requester_id: ID of the user making the request
            requester_role: Role of the requester
            
        Returns:
            True if enrollment successful
            
        Raises:
            ValueError: If validation fails
        """
        logger.info(
            f"[ENROLL_STUDENT] Requester {requester_id} enrolling "
            f"student {student_id} in course {course_id}"
        )
        
        # Validate course exists
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Validate student exists and is actually a student
        student = await self.user_repository.find_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        if student.role != UserRole.STUDENT:
            raise ValueError("User is not a student")
        
        # Validate permissions
        if not self._can_enroll(requester_id, requester_role, course):
            logger.warning(
                f"[ENROLL_DENIED] User {requester_id} cannot enroll students in course {course_id}"
            )
            raise ValueError("Insufficient permissions to enroll students in this course")
        
        # Validate course is not archived
        if course.status == CourseStatus.ARCHIVED:
            raise ValueError("Cannot enroll students in an archived course")
        
        # Enroll student
        result = await self.course_repository.enroll_student(course_id, student_id)
        
        if result:
            logger.info(f"[STUDENT_ENROLLED] Student {student_id} enrolled in course {course_id}")
        else:
            logger.warning(f"[ALREADY_ENROLLED] Student {student_id} already in course {course_id}")
        
        return result
    
    def _can_enroll(self, requester_id: str, requester_role: UserRole, course) -> bool:
        """Check if requester can enroll students in this course"""
        # Admins can enroll anyone
        if requester_role == UserRole.ADMIN:
            return True
        
        # Course teacher can enroll students
        if requester_role == UserRole.PROFESSOR and course.teacher_id == requester_id:
            return True
        
        return False

