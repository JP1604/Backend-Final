from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.course import Course


class CourseRepository(ABC):
    """Repository interface for Course entity"""
    
    @abstractmethod
    async def save(self, course: Course) -> Course:
        """Save a new course"""
        pass
    
    @abstractmethod
    async def find_by_id(self, course_id: str) -> Optional[Course]:
        """Find a course by its ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Course]:
        """Get all courses"""
        pass
    
    @abstractmethod
    async def find_by_teacher(self, teacher_id: str) -> List[Course]:
        """Find all courses taught by a teacher"""
        pass
    
    @abstractmethod
    async def find_by_student(self, student_id: str) -> List[Course]:
        """Find all courses a student is enrolled in"""
        pass
    
    @abstractmethod
    async def update(self, course: Course) -> Course:
        """Update an existing course"""
        pass
    
    @abstractmethod
    async def delete(self, course_id: str) -> None:
        """Delete a course"""
        pass
    
    @abstractmethod
    async def enroll_student(self, course_id: str, student_id: str) -> bool:
        """Enroll a student in a course"""
        pass
    
    @abstractmethod
    async def unenroll_student(self, course_id: str, student_id: str) -> bool:
        """Remove a student from a course"""
        pass
    
    @abstractmethod
    async def get_students(self, course_id: str) -> List[str]:
        """Get all student IDs enrolled in a course"""
        pass
    
    @abstractmethod
    async def assign_challenge(self, course_id: str, challenge_id: str, order_index: int = 0) -> bool:
        """Assign a challenge to a course"""
        pass
    
    @abstractmethod
    async def unassign_challenge(self, course_id: str, challenge_id: str) -> bool:
        """Remove a challenge assignment from a course"""
        pass
    
    @abstractmethod
    async def get_challenges(self, course_id: str) -> List[str]:
        """Get all challenge IDs assigned to a course"""
        pass

