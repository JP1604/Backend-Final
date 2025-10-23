import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..infrastructure.repositories.submission_repository_impl import SubmissionRepositoryImpl
from ..infrastructure.persistence.models import SubmissionModel
from ..domain.entities.submission import SubmissionStatus, TestCaseResult
from .celery_app import celery_app

# Database setup
DATABASE_URL = "postgresql://postgres:password@postgres:5432/online_judge"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_submission(self, submission_id: str, challenge_id: str, language: str, code: str):
    """Process a code submission - SIMPLIFIED VERSION"""
    logger.info(f"Processing submission {submission_id} for challenge {challenge_id} in {language}")
    
    try:
        # Create database session
        db = SessionLocal()
        
        try:
            # Get submission
            submission_repo = SubmissionRepositoryImpl(db)
            submission = asyncio.run(submission_repo.find_by_id(submission_id))
            
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            # Update status to RUNNING
            submission.status = SubmissionStatus.RUNNING
            submission.updated_at = datetime.utcnow()
            asyncio.run(submission_repo.update(submission))
            
            # SIMPLE SIMULATION - Just wait a bit and return success
            import time
            time.sleep(2)  # Wait 2 seconds
            
            # Create simple test results
            cases = [
                TestCaseResult(case_id=1, status=SubmissionStatus.ACCEPTED, time_ms=100),
                TestCaseResult(case_id=2, status=SubmissionStatus.ACCEPTED, time_ms=150),
                TestCaseResult(case_id=3, status=SubmissionStatus.ACCEPTED, time_ms=200)
            ]
            
            # Update submission with SUCCESS result
            submission.status = SubmissionStatus.ACCEPTED
            submission.score = 100
            submission.time_ms_total = 450
            submission.cases = cases
            submission.updated_at = datetime.utcnow()
            
            asyncio.run(submission_repo.update(submission))
            
            logger.info(f"Submission {submission_id} processed successfully")
            return {"status": "success", "submission_id": submission_id}
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)