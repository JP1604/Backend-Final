"""
Redis Queue Service for handling code submission jobs
"""
import redis
import json
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RedisQueueService:
    """Redis-based queue service for managing code execution jobs"""
    
    # Queue names for different programming languages
    QUEUE_PREFIX = "submission_queue"
    STATUS_PREFIX = "submission_status"
    RESULT_PREFIX = "submission_result"
    
    # Language-specific queues
    PYTHON_QUEUE = f"{QUEUE_PREFIX}:python"
    JAVA_QUEUE = f"{QUEUE_PREFIX}:java"
    NODEJS_QUEUE = f"{QUEUE_PREFIX}:nodejs"
    CPP_QUEUE = f"{QUEUE_PREFIX}:cpp"
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Redis connection is working"""
        try:
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def _get_queue_name(self, language: str) -> str:
        """Get the appropriate queue name for a programming language"""
        queue_map = {
            "python": self.PYTHON_QUEUE,
            "java": self.JAVA_QUEUE,
            "nodejs": self.NODEJS_QUEUE,
            "cpp": self.CPP_QUEUE,
        }
        return queue_map.get(language.lower(), self.PYTHON_QUEUE)
    
    async def enqueue_submission(
        self,
        submission_id: str,
        challenge_id: str,
        user_id: str,
        language: str,
        code: str,
        test_cases: list
    ) -> bool:
        """
        Add a code submission to the appropriate language queue
        
        Args:
            submission_id: Unique submission identifier
            challenge_id: Challenge identifier
            user_id: User identifier
            language: Programming language (python, java, nodejs, cpp)
            code: Source code to execute
            test_cases: List of test cases to run
            
        Returns:
            bool: True if successfully enqueued, False otherwise
        """
        try:
            job_data = {
                "submission_id": submission_id,
                "challenge_id": challenge_id,
                "user_id": user_id,
                "language": language.lower(),
                "code": code,
                "test_cases": test_cases,
                "enqueued_at": datetime.utcnow().isoformat(),
                "status": "QUEUED"
            }
            
            queue_name = self._get_queue_name(language)
            
            # Add to queue (lpush is synchronous)
            self.redis_client.lpush(queue_name, json.dumps(job_data))
            
            # Set initial status (async method)
            await self.set_submission_status(submission_id, "QUEUED")
            
            logger.info(f"Submission {submission_id} enqueued to {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue submission {submission_id}: {str(e)}")
            return False
    
    async def dequeue_submission(self, language: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get a submission from the language-specific queue
        
        Args:
            language: Programming language queue to check
            timeout: Timeout in seconds for blocking pop
            
        Returns:
            Dict containing job data or None if queue is empty
        """
        try:
            queue_name = self._get_queue_name(language)
            result = self.redis_client.brpop(queue_name, timeout=timeout)
            
            if result:
                _, job_data_str = result
                job_data = json.loads(job_data_str)
                logger.info(f"Dequeued submission {job_data['submission_id']} from {queue_name}")
                return job_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue from {language} queue: {str(e)}")
            return None
    
    async def set_submission_status(self, submission_id: str, status: str, ttl: int = 3600):
        """
        Set the status of a submission in Redis
        
        Args:
            submission_id: Submission identifier
            status: Status string (QUEUED, RUNNING, COMPLETED, FAILED)
            ttl: Time to live in seconds (default 1 hour)
        """
        try:
            key = f"{self.STATUS_PREFIX}:{submission_id}"
            self.redis_client.setex(key, ttl, status)
            logger.debug(f"Status for {submission_id} set to {status}")
        except Exception as e:
            logger.error(f"Failed to set status for {submission_id}: {str(e)}")
    
    async def get_submission_status(self, submission_id: str) -> Optional[str]:
        """Get the status of a submission from Redis"""
        try:
            key = f"{self.STATUS_PREFIX}:{submission_id}"
            status = self.redis_client.get(key)
            return status
        except Exception as e:
            logger.error(f"Failed to get status for {submission_id}: {str(e)}")
            return None
    
    async def set_submission_result(
        self,
        submission_id: str,
        result: Dict[str, Any],
        ttl: int = 3600
    ):
        """
        Store the execution result of a submission
        
        Args:
            submission_id: Submission identifier
            result: Result dictionary containing test results, score, etc.
            ttl: Time to live in seconds (default 1 hour)
        """
        try:
            key = f"{self.RESULT_PREFIX}:{submission_id}"
            self.redis_client.setex(key, ttl, json.dumps(result))
            logger.info(f"Result stored for submission {submission_id}")
        except Exception as e:
            logger.error(f"Failed to store result for {submission_id}: {str(e)}")
    
    async def get_submission_result(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get the execution result of a submission from Redis"""
        try:
            key = f"{self.RESULT_PREFIX}:{submission_id}"
            result_str = self.redis_client.get(key)
            if result_str:
                return json.loads(result_str)
            return None
        except Exception as e:
            logger.error(f"Failed to get result for {submission_id}: {str(e)}")
            return None
    
    async def get_queue_length(self, language: str) -> int:
        """Get the number of jobs in a language-specific queue"""
        try:
            queue_name = self._get_queue_name(language)
            length = self.redis_client.llen(queue_name)
            return length
        except Exception as e:
            logger.error(f"Failed to get queue length for {language}: {str(e)}")
            return 0
    
    async def get_all_queue_lengths(self) -> Dict[str, int]:
        """Get the lengths of all language queues"""
        return {
            "python": await self.get_queue_length("python"),
            "java": await self.get_queue_length("java"),
            "nodejs": await self.get_queue_length("nodejs"),
            "cpp": await self.get_queue_length("cpp"),
        }
    
    def clear_queue(self, language: str):
        """Clear all jobs from a language-specific queue (for testing/maintenance)"""
        try:
            queue_name = self._get_queue_name(language)
            self.redis_client.delete(queue_name)
            logger.warning(f"Cleared queue: {queue_name}")
        except Exception as e:
            logger.error(f"Failed to clear queue {language}: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    async def peek_queue(self, language: str, start: int = 0, end: int = -1) -> List[Dict[str, Any]]:
        """
        Peek at submissions in a language queue without removing them
        
        Args:
            language: Programming language queue to peek
            start: Start index (0-based)
            end: End index (-1 for all, or specific index)
            
        Returns:
            List of submission job data dictionaries
        """
        try:
            queue_name = self._get_queue_name(language)
            # LRANGE returns items from start to end (inclusive)
            # Note: Redis lists are right-to-left for RPOP, so index 0 is the oldest
            items = self.redis_client.lrange(queue_name, start, end)
            
            submissions = []
            for item in items:
                try:
                    job_data = json.loads(item)
                    submissions.append(job_data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse queue item: {item}")
                    continue
            
            logger.debug(f"Peeked {len(submissions)} items from {queue_name}")
            return submissions
            
        except Exception as e:
            logger.error(f"Failed to peek queue {language}: {str(e)}")
            return []
    
    async def peek_all_queues(self, limit_per_queue: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Peek at all language queues
        
        Args:
            limit_per_queue: Maximum number of items to return per queue
            
        Returns:
            Dictionary mapping language to list of submissions
        """
        languages = ["python", "java", "nodejs", "cpp"]
        result = {}
        
        for lang in languages:
            # Get up to limit_per_queue items (0 to limit-1)
            submissions = await self.peek_queue(lang, 0, limit_per_queue - 1)
            result[lang] = submissions
        
        return result

