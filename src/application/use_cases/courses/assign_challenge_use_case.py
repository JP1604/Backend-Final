"""
Assign Challenge to Course Use Case
"""
import logging
from domain.entities.user import UserRole
from domain.repositories.course_repository import CourseRepository
from domain.repositories.challenge_repository import ChallengeRepository

logger = logging.getLogger(__name__)


class AssignChallengeUseCase:
    """Use case for assigning a challenge to a course"""
    
    def __init__(
        self,
        course_repository: CourseRepository,
        challenge_repository: ChallengeRepository
    ):
        self.course_repository = course_repository
        self.challenge_repository = challenge_repository
    
    async def execute(
        self,
        course_id: str,
        challenge_id: str,
        order_index: int,
        requester_id: str,
        requester_role: UserRole
    ) -> bool:
        """
        Assign a challenge to a course
        
        Args:
            course_id: ID of the course
            challenge_id: ID of the challenge to assign
            order_index: Display order of the challenge
            requester_id: ID of the user making the request
            requester_role: Role of the requester
            
        Returns:
            True if assignment successful
            
        Raises:
            ValueError: If validation fails
        """
        logger.info(
            f"[ASSIGN_CHALLENGE] User {requester_id} assigning "
            f"challenge {challenge_id} to course {course_id}"
        )
        
        # Validate course exists
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Validate challenge exists
        challenge = await self.challenge_repository.find_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")
        
        # Validate permissions
        if not course.can_be_managed_by(requester_id, requester_role):
            logger.warning(
                f"[ASSIGN_DENIED] User {requester_id} cannot manage course {course_id}"
            )
            raise ValueError("Insufficient permissions to assign challenges to this course")
        
        # Validate challenge is published or user is admin/teacher
        if not challenge.is_published() and requester_role == UserRole.STUDENT:
            raise ValueError("Cannot assign unpublished challenges")
        
        # Assign challenge
        result = await self.course_repository.assign_challenge(
            course_id,
            challenge_id,
            order_index
        )
        
        if result:
            logger.info(
                f"[CHALLENGE_ASSIGNED] Challenge {challenge_id} assigned to course {course_id}"
            )
        else:
            logger.warning(
                f"[ALREADY_ASSIGNED] Challenge {challenge_id} already assigned to course {course_id}"
            )
        
        return result

