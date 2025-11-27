"""
Assign Challenge to Exam Use Case
Allows professors/admins to assign challenges to exams with points
"""
import logging
from typing import Optional
from domain.entities.user import UserRole
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl
from infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from infrastructure.persistence.models import exam_challenges
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AssignChallengeToExamUseCase:
    """Use case for assigning a challenge to an exam"""
    
    def __init__(
        self,
        exam_repository: ExamRepositoryImpl,
        course_repository: CourseRepositoryImpl,
        challenge_repository: ChallengeRepositoryImpl
    ):
        self.exam_repository = exam_repository
        self.course_repository = course_repository
        self.challenge_repository = challenge_repository
    
    async def execute(
        self,
        exam_id: str,
        challenge_id: str,
        points: int = 100,
        order_index: int = 0,
        requester_id: str = None,
        requester_role: UserRole = None
    ) -> bool:
        """
        Assign a challenge to an exam with specified points
        
        Args:
            exam_id: ID of the exam
            challenge_id: ID of the challenge to assign
            points: Points this challenge is worth in the exam (default: 100)
            order_index: Display order of the challenge in the exam
            requester_id: ID of the user making the request
            requester_role: Role of the user making the request
            
        Returns:
            True if assignment was successful, False if already assigned
            
        Raises:
            ValueError: If validation fails or insufficient permissions
        """
        logger.info(
            f"[ASSIGN_CHALLENGE_TO_EXAM] Assigning challenge {challenge_id} "
            f"to exam {exam_id} with {points} points"
        )
        
        # Validate permissions
        if requester_role and not self._can_manage_exam(requester_role):
            logger.warning(f"[ASSIGN_DENIED] User {requester_id} lacks permission (role: {requester_role})")
            raise ValueError("Only professors and administrators can assign challenges to exams")
        
        # Verify exam exists
        exam = await self.exam_repository.get_exam_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        # Verify challenge exists
        challenge = await self.challenge_repository.find_by_id(challenge_id)
        if not challenge:
            raise ValueError(f"Challenge {challenge_id} not found")
        
        # Check if user can manage this exam's course
        if requester_id and requester_role:
            course = await self.course_repository.find_by_id(exam.course_id)
            if not course:
                raise ValueError(f"Course {exam.course_id} not found")
            
            if not exam.can_be_managed_by(requester_id, course.teacher_id, requester_role):
                raise ValueError("You can only assign challenges to exams in courses you teach")
        
        # Validate points
        if points < 0:
            raise ValueError("Points must be non-negative")
        
        # Check if already assigned
        db = self.exam_repository.db
        existing = db.execute(
            select(exam_challenges).where(
                exam_challenges.c.exam_id == exam_id,
                exam_challenges.c.challenge_id == challenge_id
            )
        ).first()
        
        if existing:
            logger.warning(
                f"[ALREADY_ASSIGNED] Challenge {challenge_id} already assigned to exam {exam_id}"
            )
            return False
        
        # Insert assignment
        db.execute(
            exam_challenges.insert().values(
                exam_id=exam_id,
                challenge_id=challenge_id,
                points=points,
                order_index=order_index
            )
        )
        db.commit()
        
        logger.info(
            f"[CHALLENGE_ASSIGNED] Challenge {challenge_id} assigned to exam {exam_id} "
            f"with {points} points"
        )
        return True
    
    def _can_manage_exam(self, user_role: UserRole) -> bool:
        """Check if user role can manage exams"""
        return user_role in [UserRole.PROFESSOR, UserRole.ADMIN]

