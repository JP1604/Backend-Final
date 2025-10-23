"""
Use case for enqueuing a submission to the execution queue
"""
import logging
from datetime import datetime
from typing import List

from ...domain.repositories.challenge_repository import ChallengeRepository
from ...application.dtos.execution_dto import (
    EnqueueSubmissionDTO,
    SubmissionJobDTO,
    TestCaseDTO
)

logger = logging.getLogger(__name__)


class EnqueueSubmissionUseCase:
    """
    Use case for enqueuing a submission for execution
    
    Responsibilities:
    1. Validate submission can be enqueued
    2. Fetch test cases for challenge
    3. Create job DTO
    4. Return job data for queueing
    """
    
    def __init__(
        self,
        challenge_repository: ChallengeRepository
    ):
        self.challenge_repository = challenge_repository
    
    async def execute(
        self,
        request: EnqueueSubmissionDTO
    ) -> tuple[bool, SubmissionJobDTO | None, str]:
        """
        Prepare submission for enqueuing
        
        Args:
            request: Enqueue submission request
            
        Returns:
            Tuple of (success, job_dto, error_message)
        """
        try:
            # 1. Validate challenge exists
            challenge = await self.challenge_repository.find_by_id(request.challenge_id)
            if not challenge:
                return False, None, "Challenge not found"
            
            # 2. Get test cases
            test_cases = await self.challenge_repository.get_test_cases(request.challenge_id)
            if not test_cases:
                return False, None, "No test cases found for challenge"
            
            # 3. Convert to DTOs
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
            
            # 4. Create job DTO
            job = SubmissionJobDTO(
                submission_id=request.submission_id,
                challenge_id=request.challenge_id,
                user_id=request.user_id,
                language=request.language,
                code=request.code,
                test_cases=test_case_dtos,
                enqueued_at=datetime.utcnow()
            )
            
            logger.info(
                f"Prepared submission {request.submission_id} for queueing: "
                f"{len(test_case_dtos)} test cases"
            )
            
            return True, job, ""
            
        except Exception as e:
            error_msg = f"Error preparing submission for queue: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg

