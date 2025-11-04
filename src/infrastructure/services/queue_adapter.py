"""
Adapter for queue operations
Bridge between application layer (use cases) and infrastructure (Redis)
"""
import logging
from typing import Optional
from dataclasses import asdict

from ...application.dtos.execution_dto import (
    SubmissionJobDTO,
    ExecutionResultDTO,
    TestCaseDTO
)

logger = logging.getLogger(__name__)


class QueueAdapter:
    """
    Adapter that converts between application DTOs and Redis queue format
    """
    
    def __init__(self, redis_queue_service):
        """
        Initialize with Redis queue service
        
        Args:
            redis_queue_service: Instance of RedisQueueService
        """
        self.queue_service = redis_queue_service
    
    async def enqueue_submission(self, job: SubmissionJobDTO) -> bool:
        """
        Enqueue a submission job
        
        Args:
            job: Submission job DTO
            
        Returns:
            True if successfully enqueued, False otherwise
        """
        try:
            # Convert DTOs to plain dicts for Redis
            test_cases = [
                {
                    "id": tc.id,
                    "input": tc.input,
                    "expected_output": tc.expected_output,
                    "is_hidden": tc.is_hidden,
                    "order_index": tc.order_index
                }
                for tc in job.test_cases
            ]
            
            return await self.queue_service.enqueue_submission(
                submission_id=job.submission_id,
                challenge_id=job.challenge_id,
                user_id=job.user_id,
                language=job.language,
                code=job.code,
                test_cases=test_cases
            )
            
        except Exception as e:
            logger.error(f"Error enqueuing submission {job.submission_id}: {str(e)}")
            return False
    
    async def set_submission_status(self, submission_id: str, status: str) -> bool:
        """Set submission status in cache"""
        try:
            await self.queue_service.set_submission_status(submission_id, status)
            return True
        except Exception as e:
            logger.error(f"Error setting status for {submission_id}: {str(e)}")
            return False
    
    async def get_submission_status(self, submission_id: str) -> Optional[str]:
        """Get submission status from cache"""
        try:
            return await self.queue_service.get_submission_status(submission_id)
        except Exception as e:
            logger.error(f"Error getting status for {submission_id}: {str(e)}")
            return None
    
    async def cache_execution_result(self, result: ExecutionResultDTO) -> bool:
        """
        Cache execution result in Redis
        
        Args:
            result: Execution result DTO
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            # Convert DTO to dict
            result_dict = {
                "submission_id": result.submission_id,
                "status": result.status,
                "score": result.score,
                "total_time_ms": result.total_time_ms,
                "language": result.language,
                "error_message": result.error_message,
                "cases": [
                    {
                        "case_id": case.case_id,
                        "status": case.status,
                        "time_ms": case.time_ms,
                        "memory_mb": case.memory_mb,
                        "output": case.output,
                        "expected_output": case.expected_output,
                        "error_message": case.error_message
                    }
                    for case in result.cases
                ]
            }
            
            await self.queue_service.set_submission_result(
                result.submission_id,
                result_dict
            )
            await self.queue_service.set_submission_status(
                result.submission_id,
                result.status
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Error caching result for {result.submission_id}: {str(e)}"
            )
            return False
    
    async def get_queue_length(self, language: str) -> int:
        """Get the number of pending jobs for a language"""
        try:
            return await self.queue_service.get_queue_length(language)
        except Exception as e:
            logger.error(f"Error getting queue length for {language}: {str(e)}")
            return 0

