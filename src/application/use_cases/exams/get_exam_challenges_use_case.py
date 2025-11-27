"""
Get Exam Challenges Use Case
Retrieves all challenges assigned to an exam with their points
"""
import logging
from typing import List, Dict
from infrastructure.repositories.exam_repository_impl import ExamRepositoryImpl
from infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from infrastructure.persistence.models import exam_challenges
from sqlalchemy import select

logger = logging.getLogger(__name__)


class GetExamChallengesUseCase:
    """Use case for retrieving challenges assigned to an exam"""
    
    def __init__(
        self,
        exam_repository: ExamRepositoryImpl,
        challenge_repository: ChallengeRepositoryImpl
    ):
        self.exam_repository = exam_repository
        self.challenge_repository = challenge_repository
    
    async def execute(self, exam_id: str) -> List[Dict]:
        """
        Get all challenges assigned to an exam with their points and order
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of dictionaries with challenge info and points
            
        Raises:
            ValueError: If exam not found
        """
        logger.info(f"[GET_EXAM_CHALLENGES] Retrieving challenges for exam {exam_id}")
        
        # Verify exam exists
        exam = await self.exam_repository.get_exam_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        # Get exam challenges with points
        db = self.exam_repository.db
        rows = db.execute(
            select(exam_challenges).where(
                exam_challenges.c.exam_id == exam_id
            ).order_by(exam_challenges.c.order_index)
        ).fetchall()
        
        challenges = []
        for row in rows:
            challenge_id = str(row.challenge_id)
            challenge = await self.challenge_repository.find_by_id(challenge_id)
            
            if challenge:
                challenges.append({
                    "challenge_id": challenge_id,
                    "title": challenge.title,
                    "description": challenge.description,
                    "difficulty": challenge.difficulty,
                    "points": int(row.points or 0),
                    "order_index": int(row.order_index or 0)
                })
        
        logger.info(f"[EXAM_CHALLENGES_RETRIEVED] Found {len(challenges)} challenges for exam {exam_id}")
        return challenges

