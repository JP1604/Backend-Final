"""
Update Course Use Case
"""
import logging
from datetime import datetime
from typing import Optional

from domain.entities.course import Course, CourseStatus
from domain.entities.user import UserRole
from domain.repositories.course_repository import CourseRepository

logger = logging.getLogger(__name__)


class UpdateCourseUseCase:
    """Use case for updating an existing course"""
    
    def __init__(self, course_repository: CourseRepository):
        self.course_repository = course_repository
    
    async def execute(
        self,
        course_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[CourseStatus] = None,
        requester_id: str = None,
        requester_role: UserRole = None
    ) -> Course:
        """
        Update an existing course
        
        Args:
            course_id: ID of the course to update
            name: New course name (optional)
            description: New course description (optional)
            start_date: New start date (optional)
            end_date: New end date (optional)
            status: New status (optional)
            requester_id: ID of the user making the request
            requester_role: Role of the requester
            
        Returns:
            Updated course entity
            
        Raises:
            ValueError: If validation fails or insufficient permissions
        """
        logger.info(f"[UPDATE_COURSE] User {requester_id} updating course: {course_id}")
        
        # Get existing course
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Validate permissions
        if not course.can_be_managed_by(requester_id, requester_role):
            logger.warning(f"[UPDATE_COURSE_DENIED] User {requester_id} lacks permission")
            raise ValueError("Insufficient permissions to update this course")
        
        # Update fields if provided
        if name is not None:
            if not name.strip():
                raise ValueError("Course name cannot be empty")
            if len(name) > 255:
                raise ValueError("Course name must be 255 characters or less")
            course.name = name.strip()
        
        if description is not None:
            course.description = description.strip() if description else None
        
        if start_date is not None:
            course.start_date = start_date
        
        if end_date is not None:
            course.end_date = end_date
        
        if status is not None:
            course.status = status
        
        # Validate dates if both provided
        if course.start_date and course.end_date:
            if course.end_date <= course.start_date:
                raise ValueError("End date must be after start date")
        
        course.updated_at = datetime.utcnow()
        
        # Save to repository
        updated_course = await self.course_repository.update(course)
        
        logger.info(f"[COURSE_UPDATED] Course {updated_course.id} updated by {requester_id}")
        
        return updated_course

