"""
Create Course Use Case
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from domain.entities.course import Course, CourseStatus
from domain.entities.user import UserRole
from domain.repositories.course_repository import CourseRepository

logger = logging.getLogger(__name__)


class CreateCourseUseCase:
    """Use case for creating a new course"""
    
    def __init__(self, course_repository: CourseRepository):
        self.course_repository = course_repository
    
    async def execute(
        self,
        name: str,
        description: Optional[str],
        teacher_id: str,
        user_role: UserRole,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: CourseStatus = CourseStatus.DRAFT
    ) -> Course:
        """
        Create a new course
        
        Args:
            name: Course name
            description: Course description
            teacher_id: ID of the teacher creating the course
            user_role: Role of the user creating the course
            start_date: Optional start date
            end_date: Optional end date
            status: Initial course status
            
        Returns:
            Created course entity
            
        Raises:
            ValueError: If validation fails or insufficient permissions
        """
        logger.info(f"[CREATE_COURSE] User {teacher_id} creating course: {name}")
        
        # Validate permissions
        if not self._can_create_course(user_role):
            logger.warning(f"[CREATE_COURSE_DENIED] User {teacher_id} lacks permission (role: {user_role})")
            raise ValueError("Only professors and administrators can create courses")
        
        # Validate input
        self._validate_course_data(name, start_date, end_date)
        
        # Create course entity
        course = Course(
            id=str(uuid.uuid4()),
            name=name.strip(),
            description=description.strip() if description else None,
            teacher_id=teacher_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to repository
        created_course = await self.course_repository.save(course)
        
        logger.info(
            f"[COURSE_CREATED] Course {created_course.id} '{created_course.name}' "
            f"created by {teacher_id}"
        )
        
        return created_course
    
    def _can_create_course(self, user_role: UserRole) -> bool:
        """Check if user can create courses"""
        return user_role in [UserRole.ADMIN, UserRole.PROFESSOR]
    
    def _validate_course_data(
        self,
        name: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ):
        """Validate course data"""
        if not name or not name.strip():
            raise ValueError("Course name is required")
        
        if len(name) > 255:
            raise ValueError("Course name must be 255 characters or less")
        
        # Validate dates if both provided
        if start_date and end_date:
            if end_date <= start_date:
                raise ValueError("End date must be after start date")

