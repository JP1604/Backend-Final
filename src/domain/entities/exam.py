"""
Exam domain entity
Represents an exam/evaluation with challenges, time limits, and attempt constraints
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class ExamStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Exam:
    """
    Exam entity
    
    An exam:
    - Belongs to a course
    - Contains multiple challenges
    - Has time limits (start/end time, duration)
    - Has attempt limits per student
    - Can have specific scoring rules
    """
    id: str
    course_id: str
    title: str
    description: str
    status: ExamStatus
    
    # Time constraints
    start_time: datetime
    end_time: datetime
    duration_minutes: int  # Max time per student from when they start
    
    # Attempt constraints
    max_attempts: int = 1  # How many times a student can take the exam
    
    # Scoring
    passing_score: Optional[int] = None  # Minimum score to pass (0-100)
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = None  # Teacher user ID
    
    def is_active(self) -> bool:
        """Check if exam is currently active and accepting submissions"""
        if self.status != ExamStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time
    
    def can_student_start(self, current_attempts: int) -> tuple[bool, str]:
        """
        Check if a student can start the exam
        
        Returns:
            (can_start: bool, reason: str)
        """
        if not self.is_active():
            return False, "Exam is not currently active"
        
        if current_attempts >= self.max_attempts:
            return False, f"Maximum attempts ({self.max_attempts}) reached"
        
        now = datetime.utcnow()
        if now < self.start_time:
            return False, "Exam has not started yet"
        
        if now > self.end_time:
            return False, "Exam has ended"
        
        return True, "OK"
    
    def is_passing_score(self, score: int) -> bool:
        """Check if a score is passing"""
        if self.passing_score is None:
            return True  # No minimum score requirement
        return score >= self.passing_score
    
    def can_be_managed_by(self, user_id: str, course_teacher_id: str, user_role) -> bool:
        """Check if user can manage this exam"""
        from domain.entities.user import UserRole
        
        # Admins can manage any exam
        if user_role == UserRole.ADMIN:
            return True
        
        # Course teacher can manage exams in their course
        if user_role == UserRole.PROFESSOR and course_teacher_id == user_id:
            return True
        
        return False
    
    def __repr__(self):
        return f"Exam(id={self.id}, title={self.title}, course_id={self.course_id}, status={self.status})"

