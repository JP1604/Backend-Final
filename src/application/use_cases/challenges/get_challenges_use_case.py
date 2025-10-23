from typing import List, Dict, Optional
from ....domain.entities.challenge import Challenge
from ....domain.entities.user import UserRole
from ....domain.repositories.challenge_repository import ChallengeRepository


class GetChallengesUseCase:
    def __init__(self, challenge_repository: ChallengeRepository):
        self.challenge_repository = challenge_repository

    async def execute(
        self,
        user_id: str,
        user_role: UserRole,
        course_id: Optional[str] = None,
        status: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Challenge]:
        filters = {}

        # Si es estudiante, solo puede ver challenges publicados
        if user_role == UserRole.STUDENT:
            filters["status"] = "published"

        if course_id:
            filters["course_id"] = course_id

        if status:
            filters["status"] = status

        if difficulty:
            filters["difficulty"] = difficulty

       
       
        
        challenges = await self.challenge_repository.find_all(filters)
        
        
        for i, challenge in enumerate(challenges):
            can_view = challenge.can_be_viewed_by(user_role)
            

        # Filtrar challenges que el usuario puede ver
        filtered = [
            challenge for challenge in challenges
            if challenge.can_be_viewed_by(user_role)
        ]
        
        
        return filtered
