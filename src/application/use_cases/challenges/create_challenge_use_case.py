import uuid
from datetime import datetime
from typing import Dict, Any, List
from ....domain.entities.challenge import Challenge, ChallengeDifficulty, ChallengeStatus
from ....domain.entities.user import UserRole
from ....domain.repositories.challenge_repository import ChallengeRepository


class CreateChallengeUseCase:
    def __init__(self, challenge_repository: ChallengeRepository):
        self.challenge_repository = challenge_repository

    async def execute(
        self,
        title: str,
        description: str,
        difficulty: ChallengeDifficulty,
        tags: List[str],
        time_limit: int,
        memory_limit: int,
        created_by: str,
        user_role: UserRole,
        course_id: str = None
    ) -> Challenge:
        # Validar permisos
        if not self._can_create_challenge(user_role):
            raise ValueError("Insufficient permissions to create challenges")

        # Validar datos
        self._validate_challenge_data(title, description, time_limit, memory_limit)

        # Crear challenge
        challenge = Challenge(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            difficulty=difficulty,
            tags=tags,
            time_limit=time_limit,
            memory_limit=memory_limit,
            status=ChallengeStatus.PUBLISHED,
            created_by=created_by,
            course_id=course_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        return await self.challenge_repository.save(challenge)

    def _can_create_challenge(self, user_role: UserRole) -> bool:
        return user_role in [UserRole.ADMIN, UserRole.PROFESSOR]

    def _validate_challenge_data(self, title: str, description: str, time_limit: int, memory_limit: int):
        if not title or not title.strip():
            raise ValueError("Title is required")

        if not description or not description.strip():
            raise ValueError("Description is required")

        if time_limit <= 0:
            raise ValueError("Time limit must be greater than 0")

        if memory_limit <= 0:
            raise ValueError("Memory limit must be greater than 0")
