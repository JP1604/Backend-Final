from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from infrastructure.persistence.models import ExamAttemptModel, ExamModel
from domain.entities.exam import ExamStatus

logger = logging.getLogger(__name__)
from domain.entities.exam import Exam, ExamStatus


class ExamRepositoryImpl:
    def __init__(self, db: Session):
        self.db = db

    async def get_attempts_by_exam_id(self, exam_id: str) -> List[dict]:
        rows = self.db.query(ExamAttemptModel).filter(ExamAttemptModel.exam_id == exam_id).all()
        attempts = []
        for r in rows:
            attempts.append({
                "id": str(r.id),
                "user_id": str(r.user_id),
                "score": int(r.score or 0),
                "started_at": r.started_at,
                "submitted_at": r.submitted_at,
                "passed": bool(r.passed)
            })
        return attempts

    async def create_attempt(self, exam_id: str, user_id: str) -> dict:
        """Create a new exam attempt and return its identifying info."""
        from infrastructure.persistence.models import ExamAttemptModel
        attempt = ExamAttemptModel(exam_id=exam_id, user_id=user_id)
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return {
            "id": str(attempt.id),
            "exam_id": str(attempt.exam_id),
            "user_id": str(attempt.user_id),
            "started_at": attempt.started_at
        }

    async def get_attempt_by_id(self, attempt_id: str) -> dict | None:
        r = self.db.query(ExamAttemptModel).filter(ExamAttemptModel.id == attempt_id).first()
        if not r:
            return None
        return {
            "id": str(r.id),
            "exam_id": str(r.exam_id),
            "user_id": str(r.user_id),
            "started_at": r.started_at,
            "submitted_at": r.submitted_at,
            "score": int(r.score or 0),
            "passed": bool(r.passed),
            "is_active": bool(r.is_active)
        }

    async def finalize_attempt(self, attempt_id: str, score: int, passed: bool):
        """Finalize an exam attempt: set submitted_at, score and passed flag."""
        from datetime import datetime
        r = self.db.query(ExamAttemptModel).filter(ExamAttemptModel.id == attempt_id).first()
        if not r:
            raise ValueError(f"Attempt {attempt_id} not found")
        r.submitted_at = datetime.utcnow()
        r.score = score
        r.passed = passed
        r.is_active = False
        self.db.commit()
        self.db.refresh(r)
        return {
            "id": str(r.id),
            "exam_id": str(r.exam_id),
            "user_id": str(r.user_id),
            "score": int(r.score or 0),
            "submitted_at": r.submitted_at,
            "passed": bool(r.passed)
        }

    async def get_exam_by_id(self, exam_id: str) -> Optional[Exam]:
        """Get exam by ID as domain entity"""
        r = self.db.query(ExamModel).filter(ExamModel.id == exam_id).first()
        if not r:
            return None
        return self._to_entity(r)
    
    async def get_exam_dict_by_id(self, exam_id: str) -> dict | None:
        """Get exam by ID as dictionary (for backward compatibility)"""
        r = self.db.query(ExamModel).filter(ExamModel.id == exam_id).first()
        if not r:
            return None
        # Convert status string to enum value if needed
        status_value = r.status
        if isinstance(status_value, str):
            try:
                status_value = ExamStatus(status_value.lower())
            except ValueError:
                status_value = ExamStatus.DRAFT
        
        return {
            "id": str(r.id),
            "course_id": str(r.course_id),
            "title": r.title,
            "description": r.description,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "duration_minutes": r.duration_minutes,
            "max_attempts": r.max_attempts,
            "passing_score": r.passing_score,
            "status": status_value.value if isinstance(status_value, ExamStatus) else status_value,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "created_by": str(r.created_by)
        }
    
    async def find_all(self) -> List[Exam]:
        """Get all exams"""
        rows = self.db.query(ExamModel).all()
        return [self._to_entity(r) for r in rows]
    
    async def find_by_course_id(self, course_id: str) -> List[Exam]:
        """Get all exams for a course"""
        rows = self.db.query(ExamModel).filter(ExamModel.course_id == course_id).all()
        return [self._to_entity(r) for r in rows]
    
    async def save(self, exam: Exam) -> Exam:
        """Save a new exam"""
        model = self._to_model(exam)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)
    
    async def update(self, exam: Exam) -> Exam:
        """Update an existing exam"""
        model = self.db.query(ExamModel).filter(ExamModel.id == exam.id).first()
        if not model:
            raise ValueError(f"Exam {exam.id} not found")
        
        model.title = exam.title
        model.description = exam.description
        # Convert enum to its string value for storage
        model.status = exam.status.value if isinstance(exam.status, ExamStatus) else exam.status
        model.start_time = exam.start_time
        model.end_time = exam.end_time
        model.duration_minutes = exam.duration_minutes
        model.max_attempts = exam.max_attempts
        model.passing_score = exam.passing_score
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)
    
    async def delete(self, exam_id: str) -> bool:
        """Delete an exam"""
        result = self.db.query(ExamModel).filter(ExamModel.id == exam_id).delete()
        self.db.commit()
        return result > 0
    
    def _to_entity(self, model: ExamModel) -> Exam:
        """Convert database model to domain entity"""
        # Handle status conversion - status is stored as string in DB
        status_value = model.status
        if isinstance(status_value, ExamStatus):
            status_value = status_value
        elif isinstance(status_value, str):
            # If it's a string, try to convert it to the enum
            try:
                status_value = ExamStatus(status_value.lower())
            except ValueError:
                # If conversion fails, default to DRAFT
                logger.warning(f"[EXAM_STATUS_CONVERSION] Invalid status '{status_value}', defaulting to DRAFT")
                status_value = ExamStatus.DRAFT
        
        return Exam(
            id=str(model.id),
            course_id=str(model.course_id),
            title=model.title,
            description=model.description or "",
            status=status_value,
            start_time=model.start_time,
            end_time=model.end_time,
            duration_minutes=model.duration_minutes,
            max_attempts=model.max_attempts,
            passing_score=model.passing_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=str(model.created_by)
        )
    
    def _to_model(self, entity: Exam) -> ExamModel:
        """Convert domain entity to database model"""
        # Convert enum to its string value for storage
        status_value = entity.status.value if isinstance(entity.status, ExamStatus) else entity.status
        
        return ExamModel(
            id=entity.id,
            course_id=entity.course_id,
            title=entity.title,
            description=entity.description,
            status=status_value,
            start_time=entity.start_time,
            end_time=entity.end_time,
            duration_minutes=entity.duration_minutes,
            max_attempts=entity.max_attempts,
            passing_score=entity.passing_score,
            created_by=entity.created_by
        )

    async def get_exams_by_course_id(self, course_id: str) -> List[dict]:
        """Get all exams for a specific course"""
        from infrastructure.persistence.models import ExamModel
        rows = self.db.query(ExamModel).filter(ExamModel.course_id == course_id).all()
        exams = []
        for r in rows:
            exams.append({
                "id": str(r.id),
                "course_id": str(r.course_id),
                "title": r.title,
                "description": r.description,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "duration_minutes": r.duration_minutes,
                "max_attempts": r.max_attempts,
                "passing_score": r.passing_score,
                "status": r.status,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            })
        return exams

    async def get_exam_scores_by_course_id(self, course_id: str) -> List[dict]:
        """Get all exam attempts with scores for all students in a course"""
        from infrastructure.persistence.models import ExamModel, ExamAttemptModel
        
        # Get all exams for the course
        exams = self.db.query(ExamModel).filter(ExamModel.course_id == course_id).all()
        
        results = []
        for exam in exams:
            # Get all attempts for this exam
            attempts = self.db.query(ExamAttemptModel).filter(
                ExamAttemptModel.exam_id == str(exam.id)
            ).all()
            
            for attempt in attempts:
                results.append({
                    "exam_id": str(exam.id),
                    "exam_title": exam.title,
                    "user_id": str(attempt.user_id),
                    "attempt_id": str(attempt.id),
                    "score": int(attempt.score or 0),
                    "passed": bool(attempt.passed),
                    "started_at": attempt.started_at,
                    "submitted_at": attempt.submitted_at,
                    "is_active": bool(attempt.is_active)
                })
        
        return results