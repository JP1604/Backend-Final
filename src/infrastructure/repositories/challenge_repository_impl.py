from typing import Optional, List
from sqlalchemy.orm import Session
from ...domain.entities.challenge import Challenge
from ...domain.repositories.challenge_repository import ChallengeRepository, TestCase
from ..persistence.models import ChallengeModel, TestCaseModel
from datetime import datetime


class ChallengeRepositoryImpl(ChallengeRepository):
    def __init__(self, db: Session):
        self.db = db

    async def find_by_id(self, challenge_id: str) -> Optional[Challenge]:
        challenge_model = self.db.query(ChallengeModel).filter(ChallengeModel.id == challenge_id).first()
        return self._to_domain(challenge_model) if challenge_model else None

    async def save(self, challenge: Challenge) -> Challenge:
        challenge_model = self._to_model(challenge)
        self.db.add(challenge_model)
        self.db.commit()
        self.db.refresh(challenge_model)
        return self._to_domain(challenge_model)

    async def update(self, challenge: Challenge) -> Challenge:
        challenge_model = self.db.query(ChallengeModel).filter(ChallengeModel.id == challenge.id).first()
        if challenge_model:
            challenge_model.title = challenge.title
            challenge_model.description = challenge.description
            challenge_model.difficulty = challenge.difficulty
            challenge_model.tags = challenge.tags
            challenge_model.time_limit = challenge.time_limit
            challenge_model.memory_limit = challenge.memory_limit
            challenge_model.status = challenge.status
            challenge_model.course_id = challenge.course_id
            challenge_model.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(challenge_model)
            return self._to_domain(challenge_model)
        return challenge

    async def delete(self, challenge_id: str) -> None:
        self.db.query(ChallengeModel).filter(ChallengeModel.id == challenge_id).delete()
        self.db.commit()

    async def find_all(self, filters: dict = None) -> List[Challenge]:
        from ...domain.entities.challenge import ChallengeStatus, ChallengeDifficulty
        
        query = self.db.query(ChallengeModel)
        
        
        
        if filters:
            if "course_id" in filters:
                query = query.filter(ChallengeModel.course_id == filters["course_id"])
            if "status" in filters:
                # Convertir string a enum si es necesario
                status_value = filters["status"]
                if isinstance(status_value, str):
                    try:
                        status_value = ChallengeStatus(status_value)
                    except ValueError:
                        pass  # Si no es un valor válido, dejarlo como string
                query = query.filter(ChallengeModel.status == status_value)
            if "difficulty" in filters:
                difficulty_value = filters["difficulty"]
                if isinstance(difficulty_value, str):
                    try:
                        difficulty_value = ChallengeDifficulty(difficulty_value)
                    except ValueError:
                        pass
                query = query.filter(ChallengeModel.difficulty == difficulty_value)
            if "created_by" in filters:
                query = query.filter(ChallengeModel.created_by == filters["created_by"])

        challenge_models = query.all()
        
        for model in challenge_models:
            print(f"REPO DEBUG - Model: id={model.id}, status='{model.status}'")
        
        return [self._to_domain(challenge_model) for challenge_model in challenge_models]

    def _to_domain(self, challenge_model: ChallengeModel) -> Challenge:
        return Challenge(
            id=str(challenge_model.id),
            title=challenge_model.title,
            description=challenge_model.description,
            difficulty=challenge_model.difficulty,
            tags=challenge_model.tags,
            time_limit=challenge_model.time_limit,
            memory_limit=challenge_model.memory_limit,
            status=challenge_model.status,
            created_by=str(challenge_model.created_by),
            course_id=str(challenge_model.course_id) if challenge_model.course_id else None,
            created_at=challenge_model.created_at,
            updated_at=challenge_model.updated_at
        )

    def _to_model(self, challenge: Challenge) -> ChallengeModel:
        return ChallengeModel(
            id=challenge.id,
            title=challenge.title,
            description=challenge.description,
            difficulty=challenge.difficulty,
            tags=challenge.tags,
            time_limit=challenge.time_limit,
            memory_limit=challenge.memory_limit,
            status=challenge.status,
            created_by=challenge.created_by,
            course_id=challenge.course_id,
            created_at=challenge.created_at,
            updated_at=challenge.updated_at
        )
    
    async def get_test_cases(self, challenge_id: str) -> List[TestCase]:
        """Get all test cases for a challenge ordered by order_index"""
        test_case_models = (
            self.db.query(TestCaseModel)
            .filter(TestCaseModel.challenge_id == challenge_id)
            .order_by(TestCaseModel.order_index)
            .all()
        )
        
        return [
            TestCase(
                id=str(tc.id),
                challenge_id=str(tc.challenge_id),
                input=tc.input,
                expected_output=tc.expected_output,
                is_hidden=tc.is_hidden,
                order_index=tc.order_index
            )
            for tc in test_case_models
        ]
