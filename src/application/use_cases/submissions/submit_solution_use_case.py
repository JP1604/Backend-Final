import uuid
from datetime import datetime
from typing import Dict, Any
from domain.entities.submission import Submission, SubmissionStatus, ProgrammingLanguage
from domain.entities.user import UserRole
from domain.repositories.challenge_repository import ChallengeRepository
from domain.repositories.submission_repository import SubmissionRepository


class SubmitSolutionUseCase:
    def __init__(
        self,
        challenge_repository: ChallengeRepository,
        submission_repository: SubmissionRepository,
        job_queue_service
    ):
        self.challenge_repository = challenge_repository
        self.submission_repository = submission_repository
        self.job_queue_service = job_queue_service

    async def execute(
        self,
        user_id: str,
        user_role: UserRole,
        challenge_id: str,
        language: ProgrammingLanguage,
        code: str
    ) -> Submission:
        # Validar que el challenge existe
        challenge = await self.challenge_repository.find_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        # Validar que el challenge está publicado
        if not challenge.is_published():
            raise ValueError("Challenge is not available for submissions")

        # Validar que el usuario puede acceder al challenge
        if not challenge.can_be_viewed_by(user_role):
            raise ValueError("Access denied to this challenge")

        # Validar código
        self._validate_code(code)

        # Crear submission
        submission = Submission(
            id=str(uuid.uuid4()),
            user_id=user_id,
            challenge_id=challenge_id,
            language=language,
            code=code,
            status=SubmissionStatus.QUEUED,
            score=0,
            time_ms_total=0,
            cases=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Guardar submission
        saved_submission = await self.submission_repository.save(submission)

        # Encolar para procesamiento
        await self.job_queue_service.add_job({
            "submission_id": saved_submission.id,
            "challenge_id": challenge_id,
            "language": language,
            "code": code
        })

        return saved_submission

    def _validate_code(self, code: str):
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        if len(code) > 10000:
            raise ValueError("Code is too long")
