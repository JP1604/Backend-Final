import redis
import json
import os


class JobQueueService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )

    async def add_job(self, job_data: dict) -> None:
        """Add a job to the Redis queue"""
        job_id = f"submission:{job_data['submission_id']}"
        self.redis_client.lpush("submission_queue", json.dumps(job_data))
        print(f"Job added to queue: {job_id}")

    async def get_job(self) -> dict:
        """Get a job from the Redis queue"""
        job_data = self.redis_client.brpop("submission_queue", timeout=1)
        if job_data:
            return json.loads(job_data[1])
        return None

    async def mark_job_completed(self, job_id: str) -> None:
        """Mark a job as completed"""
        self.redis_client.set(f"job_status:{job_id}", "completed")

    async def mark_job_failed(self, job_id: str, error: str) -> None:
        """Mark a job as failed"""
        self.redis_client.set(f"job_status:{job_id}", f"failed:{error}")
