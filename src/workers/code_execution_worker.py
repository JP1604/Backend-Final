"""
Main code execution worker that processes submissions from Redis queues
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from workers.redis_queue_service import RedisQueueService
from workers.language_executors import (
    PythonExecutor,
    JavaExecutor,
    NodeJSExecutor,
    CppExecutor
)
from infrastructure.repositories.submission_repository_impl import SubmissionRepositoryImpl
from infrastructure.repositories.challenge_repository_impl import ChallengeRepositoryImpl
from application.use_cases.submissions.process_submission_use_case import ProcessSubmissionUseCase
from application.dtos.execution_dto import (
    SubmissionJobDTO,
    TestCaseDTO,
    ExecutionResultDTO,
    TestCaseResultDTO
)
from infrastructure.services.queue_adapter import QueueAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeExecutionWorker:
    """
    Worker that processes code submissions for a specific programming language
    
    """
    
    def __init__(self, language: str, database_url: str):
        """
        Initialize worker for a specific language
        
        Args:
            language: Programming language to process (python, java, nodejs, cpp)
            database_url: PostgreSQL database connection URL
        """
        self.language = language.upper()
        self.database_url = database_url
        self.running = False
        
        # Initialize database
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize infrastructure services
        redis_queue = RedisQueueService()
        self.queue_adapter = QueueAdapter(redis_queue)
        
        # Initialize language-specific executor
        self.executor = self._get_executor()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Initialized {self.language} worker")
    
    def _get_executor(self):
        """Get the appropriate executor for this worker's language"""
        executors = {
            "python": PythonExecutor,
            "java": JavaExecutor,
            "nodejs": NodeJSExecutor,
            "cpp": CppExecutor
        }
        
        # Convert to lowercase for lookup (language is stored as uppercase)
        language_key = self.language.lower()
        executor_class = executors.get(language_key)
        if not executor_class:
            raise ValueError(f"Unsupported language: {self.language}")
        
        return executor_class()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def start(self):
        """Start the worker and begin processing jobs"""
        self.running = True
        logger.info(f"Starting {self.language} worker...")
        
        # Check Redis connection
        if not self.queue_adapter.queue_service.health_check():
            logger.error("Redis connection failed, cannot start worker")
            return
        
        logger.info(f"{self.language} worker is running and waiting for jobs")
        
        while self.running:
            try:
                # Try to get a job from the queue (blocking with timeout)
                job_dict = await self.queue_adapter.queue_service.dequeue_submission(
                    self.language,
                    timeout=5
                )
                
                if job_dict:
                    # Convert to DTO
                    job_dto = self._dict_to_job_dto(job_dict)
                    await self._process_job(job_dto)
                else:
                    # No job available, continue loop
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retrying
        
        logger.info(f"{self.language} worker stopped")
    
    async def _process_job(self, job: SubmissionJobDTO):
        """
        Process a single submission job using clean architecture
        
        Args:
            job: Submission job DTO
        """
        logger.info(
            f"Processing submission {job.submission_id} for user {job.user_id} "
            f"(language: {job.language})"
        )
        
        db: Optional[Session] = None
        
        try:
            # Create database session
            db = self.SessionLocal()
            
            # Initialize repositories
            submission_repo = SubmissionRepositoryImpl(db)
            challenge_repo = ChallengeRepositoryImpl(db)
            
            # Initialize use case
            process_use_case = ProcessSubmissionUseCase(
                submission_repository=submission_repo,
                challenge_repository=challenge_repo
            )
            
            # Step 1: Prepare submission (via use case)
            success, execution_context = await process_use_case.execute(job)
            
            if not success or not execution_context:
                logger.error(f"Failed to prepare submission {job.submission_id}")
                return
            
            # Update status in cache
            await self.queue_adapter.set_submission_status(
                job.submission_id,
                "RUNNING"
            )
            
            # Step 2: Execute code (worker's responsibility - not business logic)
            # Validate that job language matches worker language
            job_language = job.language.upper() if isinstance(job.language, str) else str(job.language).upper()
            if job_language != self.language:
                logger.error(
                    f"Language mismatch: Worker is {self.language} but job is {job_language} "
                    f"for submission {job.submission_id}. This should not happen - check queue routing."
                )
                # Mark submission as failed
                try:
                    submission_repo = SubmissionRepositoryImpl(db)
                    submission = await submission_repo.find_by_id(job.submission_id)
                    if submission:
                        from domain.entities.submission import SubmissionStatus
                        submission.status = SubmissionStatus.RUNTIME_ERROR
                        submission.score = 0
                        submission.cases = []
                        submission.updated_at = datetime.utcnow()
                        await submission_repo.update(submission)
                except Exception as e:
                    logger.error(f"Failed to mark submission {job.submission_id} as failed: {str(e)}")
                return
            
            logger.info(f"Executing {self.language} code for submission {job.submission_id}")
            raw_result = await self.executor.execute_code(
                code=execution_context["code"],
                test_cases=execution_context["test_cases"],
                time_limit=execution_context["time_limit"],
                memory_limit=execution_context["memory_limit"]
            )
            
            # Step 3: Convert raw result to DTO
            result_dto = ExecutionResultDTO(
                submission_id=job.submission_id,
                status=raw_result["status"],
                score=raw_result["score"],
                total_time_ms=raw_result["total_time_ms"],
                language=raw_result["language"],
                error_message=raw_result.get("error_message"),
                cases=[
                    TestCaseResultDTO(
                        case_id=case["case_id"],
                        status=case["status"],
                        time_ms=case["time_ms"],
                        memory_mb=case.get("memory_mb", 0),
                        output=case.get("output"),
                        expected_output=case.get("expected_output"),
                        error_message=case.get("error_message")
                    )
                    for case in raw_result["cases"]
                ]
            )
            
            # Step 4: Complete submission (via use case)
            await process_use_case.complete(result_dto)
            
            # Step 5: Cache result
            await self.queue_adapter.cache_execution_result(result_dto)
            
            logger.info(
                f"Submission {job.submission_id} completed: "
                f"status={result_dto.status}, score={result_dto.score}"
            )
            
        except Exception as e:
            logger.error(
                f"Error processing submission {job.submission_id}: {str(e)}",
                exc_info=True
            )
            
            # Mark as failed (still through use case if possible)
            if db:
                try:
                    submission_repo = SubmissionRepositoryImpl(db)
                    submission = await submission_repo.find_by_id(job.submission_id)
                    if submission:
                        from domain.entities.submission import SubmissionStatus
                        submission.status = SubmissionStatus.RUNTIME_ERROR
                        submission.score = 0
                        submission.cases = []
                        submission.updated_at = datetime.utcnow()
                        await submission_repo.update(submission)
                except Exception as inner_e:
                    logger.error(f"Failed to mark submission as failed: {str(inner_e)}")
        
        finally:
            if db:
                db.close()
    
    def _dict_to_job_dto(self, job_dict: dict) -> SubmissionJobDTO:
        """
        Convert raw dictionary from Redis to DTO
        
        Args:
            job_dict: Raw job data from queue
            
        Returns:
            SubmissionJobDTO
        """
        test_cases = [
            TestCaseDTO(
                id=str(tc.get("id", i)),
                input=tc.get("input", ""),
                expected_output=tc.get("expected_output", ""),
                is_hidden=tc.get("is_hidden", False),
                order_index=tc.get("order_index", i)
            )
            for i, tc in enumerate(job_dict.get("test_cases", []))
        ]
        
        return SubmissionJobDTO(
            submission_id=job_dict["submission_id"],
            challenge_id=job_dict["challenge_id"],
            user_id=job_dict["user_id"],
            language=job_dict["language"],
            code=job_dict["code"],
            test_cases=test_cases,
            enqueued_at=datetime.fromisoformat(job_dict["enqueued_at"])
        )


async def main():
    """Main entry point for worker"""
    import os
    
    # Get configuration from environment
    language = os.getenv("WORKER_LANGUAGE", "python")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/online_judge"
    )
    
    logger.info(f"Starting worker for language: {language}")
    
    # Create and start worker
    worker = CodeExecutionWorker(language, database_url)
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())

