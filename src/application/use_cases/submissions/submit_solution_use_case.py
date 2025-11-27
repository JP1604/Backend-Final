import uuid
from datetime import datetime
from typing import Dict, Any
from domain.entities.submission import Submission, SubmissionStatus, ProgrammingLanguage
from domain.entities.user import UserRole
from domain.repositories.challenge_repository import ChallengeRepository
from domain.repositories.submission_repository import SubmissionRepository
from application.dtos.execution_dto import (
    EnqueueSubmissionDTO,
    SubmissionJobDTO,
    TestCaseDTO
)
import logging

logger = logging.getLogger(__name__)


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
        # Only students can submit solutions
        if user_role != UserRole.STUDENT:
            raise ValueError("Only students can submit solutions to challenges")
        
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

        # Validar que el challenge tiene test cases
        test_cases = await self.challenge_repository.get_test_cases(challenge_id)
        if not test_cases or len(test_cases) == 0:
            raise ValueError(
                "This challenge has no test cases configured. "
                "Please contact your instructor or administrator."
            )

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

        # Encolar para procesamiento - test_cases already validated above
        try:
            test_case_dtos = [
                TestCaseDTO(
                    id=str(tc.id),
                    input=tc.input,
                    expected_output=tc.expected_output,
                    is_hidden=tc.is_hidden,
                    order_index=tc.order_index
                )
                for tc in test_cases
            ]
            
            job = SubmissionJobDTO(
                submission_id=saved_submission.id,
                challenge_id=challenge_id,
                user_id=user_id,
                language=language.value,
                code=code,
                test_cases=test_case_dtos,
                enqueued_at=datetime.utcnow()
            )
            
            # Enqueue using the proper method
            enqueued = await self.job_queue_service.enqueue_submission(job)
            if not enqueued:
                logger.error(f"Failed to enqueue submission {saved_submission.id}")
                raise ValueError("Failed to enqueue submission for processing. Please try again.")
                
            logger.info(
                f"Submission {saved_submission.id} enqueued successfully "
                f"with {len(test_case_dtos)} test cases"
            )
            
        except ValueError:
            # Re-raise ValueError (like enqueue failure)
            raise
        except Exception as e:
            logger.error(f"Error enqueuing submission {saved_submission.id}: {str(e)}")
            raise ValueError(f"Error processing submission: {str(e)}")

        return saved_submission

    def _validate_code(self, code: str):
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        if len(code) > 10000:
            raise ValueError("Code is too long")
