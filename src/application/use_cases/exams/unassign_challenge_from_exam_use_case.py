"""
Unassign Challenge from Exam Use Case
Allows professors/admins to remove challenges from exams
"""
import logging
from domain.entities.user import UserRole
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl
from infrastructure.persistence.models import exam_challenges
from sqlalchemy import delete

logger = logging.getLogger(__name__)


class UnassignChallengeFromExamUseCase:
    """Use case for unassigning a challenge from an exam"""
    
    def __init__(
        self,
        exam_repository: ExamRepositoryImpl,
        course_repository: CourseRepositoryImpl
    ):
        self.exam_repository = exam_repository
        self.course_repository = course_repository
    
    async def execute(
        self,
        exam_id: str,
        challenge_id: str,
        requester_id: str = None,
        requester_role: UserRole = None
    ) -> bool:
        """
        Unassign a challenge from an exam
        
        Args:
            exam_id: ID of the exam
            challenge_id: ID of the challenge to unassign
            requester_id: ID of the user making the request
            requester_role: Role of the user making the request
            
        Returns:
            True if unassignment was successful, False if not found
            
        Raises:
            ValueError: If validation fails or insufficient permissions
        """
        logger.info(
            f"[UNASSIGN_CHALLENGE_FROM_EXAM] Unassigning challenge {challenge_id} "
            f"from exam {exam_id}"
        )
        
        # Validate permissions
        if requester_role and not self._can_manage_exam(requester_role):
            logger.warning(f"[UNASSIGN_DENIED] User {requester_id} lacks permission (role: {requester_role})")
            raise ValueError("Only professors and administrators can unassign challenges from exams")
        
        # Verify exam exists
        exam = await self.exam_repository.get_exam_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        # Check if user can manage this exam's course
        if requester_id and requester_role:
            course = await self.course_repository.find_by_id(exam.course_id)
            if not course:
                raise ValueError(f"Course {exam.course_id} not found")
            
            if not exam.can_be_managed_by(requester_id, course.teacher_id, requester_role):
                raise ValueError("You can only unassign challenges from exams in courses you teach")
        
        # Delete assignment
        db = self.exam_repository.db
        result = db.execute(
            delete(exam_challenges).where(
                exam_challenges.c.exam_id == exam_id,
                exam_challenges.c.challenge_id == challenge_id
            )
        )
        db.commit()
        
        if result.rowcount > 0:
            logger.info(
                f"[CHALLENGE_UNASSIGNED] Challenge {challenge_id} unassigned from exam {exam_id}"
            )
            return True
        else:
            logger.warning(
                f"[CHALLENGE_NOT_FOUND] Challenge {challenge_id} not assigned to exam {exam_id}"
            )
            return False
    
    def _can_manage_exam(self, user_role: UserRole) -> bool:
        """Check if user role can manage exams"""
        return user_role in [UserRole.PROFESSOR, UserRole.ADMIN]


