"""
Use case for processing a code submission
Orchestrates code execution and result storage
"""
import logging
from datetime import datetime
from typing import Optional

from domain.repositories.submission_repository import SubmissionRepository
from domain.repositories.challenge_repository import ChallengeRepository
from domain.entities.submission import SubmissionStatus, TestCaseResult
from application.dtos.execution_dto import (
    SubmissionJobDTO,
    ExecutionResultDTO,
    TestCaseResultDTO
)

logger = logging.getLogger(__name__)


class ProcessSubmissionUseCase:
    """
    Use case for processing a code submission through the execution pipeline
    
    Responsibilities:
    1. Validate submission exists
    2. Update status to RUNNING
    3. Get challenge constraints
    4. Prepare execution context
    5. Process execution results
    6. Update submission with results
    """
    
    def __init__(
        self,
        submission_repository: SubmissionRepository,
        challenge_repository: ChallengeRepository
    ):
        self.submission_repository = submission_repository
        self.challenge_repository = challenge_repository
    
    async def execute(
        self,
        job: SubmissionJobDTO
    ) -> tuple[bool, Optional[dict]]:
        """
        Process a submission job
        
        Args:
            job: Submission job data
            
        Returns:
            Tuple of (success, execution_context)
            execution_context contains challenge limits needed for execution
        """
        try:
            # 1. Validate submission exists
            submission = await self.submission_repository.find_by_id(job.submission_id)
            if not submission:
                logger.error(f"Submission {job.submission_id} not found")
                return False, None
            
            # 2. Update status to RUNNING
            submission.status = SubmissionStatus.RUNNING
            submission.updated_at = datetime.utcnow()
            await self.submission_repository.update(submission)
            
            logger.info(
                f"Submission {job.submission_id} marked as RUNNING "
                f"(user: {job.user_id}, language: {job.language})"
            )
            
            # 3. Get challenge for constraints
            challenge = await self.challenge_repository.find_by_id(job.challenge_id)
            if not challenge:
                logger.error(f"Challenge {job.challenge_id} not found")
                await self._mark_failed(
                    submission,
                    "Challenge not found"
                )
                return False, None
            
            # 4. Prepare execution context
            execution_context = {
                "submission_id": job.submission_id,
                "challenge_id": job.challenge_id,
                "user_id": job.user_id,
                "language": job.language,
                "code": job.code,
                "test_cases": [
                    {
                        "id": tc.id,
                        "input": tc.input if tc.input else None,
                        "expected_output": tc.expected_output,
                        "is_hidden": tc.is_hidden
                    }
                    for tc in job.test_cases
                ],
                "time_limit": challenge.time_limit,
                "memory_limit": challenge.memory_limit
            }
            
            return True, execution_context
            
        except Exception as e:
            logger.error(
                f"Error preparing submission {job.submission_id}: {str(e)}",
                exc_info=True
            )
            return False, None
    
    async def complete(
        self,
        result: ExecutionResultDTO
    ) -> bool:
        """
        Complete a submission with execution results
        
        Args:
            result: Execution result data
            
        Returns:
            True if successfully updated, False otherwise
        """
        try:
            # 1. Get submission
            submission = await self.submission_repository.find_by_id(result.submission_id)
            if not submission:
                logger.error(f"Submission {result.submission_id} not found for completion")
                return False
            
            # 2. Convert DTOs to domain entities
            submission.status = SubmissionStatus(result.status)
            submission.score = result.score
            submission.time_ms_total = result.total_time_ms
            submission.updated_at = datetime.utcnow()
            
            # 3. Convert test case results
            submission.cases = [
                TestCaseResult(
                    case_id=case.case_id,
                    status=SubmissionStatus(case.status),
                    time_ms=case.time_ms,
                    memory_mb=case.memory_mb,
                    error_message=case.error_message
                )
                for case in result.cases
            ]
            
            # 4. Update in repository
            await self.submission_repository.update(submission)
            
            logger.info(
                f"Submission {result.submission_id} completed: "
                f"status={result.status}, score={result.score}"
            )

            # Trigger asynchronous leaderboard recalculation for the challenge
            try:
                import asyncio
                # Lazy import to avoid circular deps in domain interfaces
                from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
                from application.use_cases.leaderboards.recalculate_challenge_leaderboard_use_case import (
                    RecalculateChallengeLeaderboardUseCase,
                )
                from sqlalchemy import select
                from infrastructure.persistence.models import course_challenges
                from application.use_cases.leaderboards.recalculate_course_leaderboard_use_case import (
                    RecalculateCourseLeaderboardUseCase,
                )
                from infrastructure.repositories.course_repository_impl import CourseRepositoryImpl

                db = getattr(self.submission_repository, 'db', None)
                if db:
                    user_repo = UserRepositoryImpl(db)
                    recalc_uc = RecalculateChallengeLeaderboardUseCase(self.submission_repository, user_repo)
                    # Schedule background task - do not await (non-blocking)
                    asyncio.create_task(recalc_uc.execute(submission.challenge_id))
                    logger.info(f"Scheduled leaderboard recalculation for challenge {submission.challenge_id}")

                    # Also schedule course leaderboard recalculation for any course that includes this challenge
                    try:
                        rows = db.execute(
                            select(course_challenges.c.course_id).where(
                                course_challenges.c.challenge_id == submission.challenge_id
                            )
                        ).fetchall()
                        course_ids = [str(r[0]) for r in rows]
                        if course_ids:
                            course_repo = CourseRepositoryImpl(db)
                            recalc_course_uc = RecalculateCourseLeaderboardUseCase(self.submission_repository, user_repo, course_repo)
                            for cid in course_ids:
                                asyncio.create_task(recalc_course_uc.execute(cid))
                                logger.info(f"Scheduled course leaderboard recalculation for course {cid}")
                    except Exception:
                        logger.debug("No course assignments found or failed to schedule course recalculation")

            except Exception as e:
                logger.warning(f"Failed to schedule leaderboard recalculation: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(
                f"Error completing submission {result.submission_id}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def _mark_failed(
        self,
        submission,
        error_message: str
    ):
        """Mark a submission as failed"""
        submission.status = SubmissionStatus.RUNTIME_ERROR
        submission.score = 0
        submission.cases = []
        submission.updated_at = datetime.utcnow()
        
        await self.submission_repository.update(submission)
        
        logger.warning(
            f"Marked submission {submission.id} as failed: {error_message}"
        )

