from typing import Optional
from domain.entities.challenge import Challenge
from domain.entities.user import UserRole
from domain.repositories.challenge_repository import ChallengeRepository


class GetChallengeUseCase:
    def __init__(self, challenge_repository: ChallengeRepository):
        self.challenge_repository = challenge_repository

    async def execute(
        self,
        challenge_id: str,
        user_id: str,
        user_role: UserRole
    ) -> Optional[Challenge]:
        """
        Get a challenge by ID
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Returns:
            Challenge if found and user has access, None otherwise
        """
        challenge = await self.challenge_repository.find_by_id(challenge_id)
        
        if not challenge:
            return None
        
        # Check if user can view this challenge
        if not challenge.can_be_viewed_by(user_role):
            return None
        
        return challenge

