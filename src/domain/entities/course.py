"""
Course domain entity
Represents a course with students, a teacher, and assigned challenges
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class CourseStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


@dataclass
class Course:
    """
    Course entity
    
    A course contains:
    - One teacher (professor)
    - Multiple students
    - Multiple challenges assigned to it
    """
    id: str
    name: str
    description: str
    teacher_id: str  # User ID of the professor
    status: CourseStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def is_active(self) -> bool:
        """Check if course is currently active"""
        if self.status != CourseStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
            
        return True
    
    def can_be_managed_by(self, user_id: str, user_role) -> bool:
        """Check if user can manage this course"""
        from domain.entities.user import UserRole
        
        # Admins can manage any course
        if user_role == UserRole.ADMIN:
            return True
        
        # Teachers can manage their own courses
        if user_role == UserRole.PROFESSOR and self.teacher_id == user_id:
            return True
        
        return False
    
    def __repr__(self):
        return f"Course(id={self.id}, name={self.name}, teacher_id={self.teacher_id}, status={self.status})"

