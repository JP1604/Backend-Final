from typing import Optional, List
from sqlalchemy.orm import Session
from domain.entities.submission import Submission, TestCaseResult
from domain.repositories.submission_repository import SubmissionRepository
from infrastructure.persistence.models import SubmissionModel
from datetime import datetime


class SubmissionRepositoryImpl(SubmissionRepository):
    def __init__(self, db: Session):
        self.db = db

    async def find_by_id(self, submission_id: str) -> Optional[Submission]:
        submission_model = self.db.query(SubmissionModel).filter(SubmissionModel.id == submission_id).first()
        return self._to_domain(submission_model) if submission_model else None

    async def save(self, submission: Submission) -> Submission:
        submission_model = self._to_model(submission)
        self.db.add(submission_model)
        self.db.commit()
        self.db.refresh(submission_model)
        return self._to_domain(submission_model)

    async def update(self, submission: Submission) -> Submission:
        submission_model = self.db.query(SubmissionModel).filter(SubmissionModel.id == submission.id).first()
        if submission_model:
            submission_model.user_id = submission.user_id
            submission_model.challenge_id = submission.challenge_id
            submission_model.language = submission.language
            submission_model.code = submission.code
            submission_model.status = submission.status
            submission_model.score = submission.score
            submission_model.time_ms_total = submission.time_ms_total
            submission_model.cases = [self._case_to_dict(case) for case in submission.cases]
            submission_model.exam_attempt_id = submission.exam_attempt_id
            submission_model.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(submission_model)
            return self._to_domain(submission_model)
        return submission

    async def delete(self, submission_id: str) -> None:
        self.db.query(SubmissionModel).filter(SubmissionModel.id == submission_id).delete()
        self.db.commit()

    async def find_by_user_id(self, user_id: str) -> List[Submission]:
        submission_models = self.db.query(SubmissionModel).filter(
            SubmissionModel.user_id == user_id
        ).order_by(SubmissionModel.created_at.desc()).all()
        return [self._to_domain(submission_model) for submission_model in submission_models]

    async def find_by_challenge_id(self, challenge_id: str) -> List[Submission]:
        submission_models = self.db.query(SubmissionModel).filter(
            SubmissionModel.challenge_id == challenge_id
        ).order_by(SubmissionModel.created_at.desc()).all()
        return [self._to_domain(submission_model) for submission_model in submission_models]

    async def find_by_user_and_challenge(self, user_id: str, challenge_id: str) -> List[Submission]:
        submission_models = self.db.query(SubmissionModel).filter(
            SubmissionModel.user_id == user_id,
            SubmissionModel.challenge_id == challenge_id
        ).order_by(SubmissionModel.created_at.desc()).all()
        return [self._to_domain(submission_model) for submission_model in submission_models]

    async def find_by_exam_attempt(self, attempt_id: str) -> List[Submission]:
        """Find all submissions for a specific exam attempt"""
        from uuid import UUID
        attempt_uuid = UUID(attempt_id)
        submission_models = self.db.query(SubmissionModel).filter(
            SubmissionModel.exam_attempt_id == attempt_uuid
        ).order_by(SubmissionModel.created_at.desc()).all()
        return [self._to_domain(submission_model) for submission_model in submission_models]

    def _to_domain(self, submission_model: SubmissionModel) -> Submission:
        cases = []
        if submission_model.cases:
            cases = [self._dict_to_case(case_data) for case_data in submission_model.cases]

        return Submission(
            id=str(submission_model.id),
            user_id=str(submission_model.user_id),
            challenge_id=str(submission_model.challenge_id),
            language=submission_model.language,
            code=submission_model.code,
            status=submission_model.status,
            score=submission_model.score,
            time_ms_total=submission_model.time_ms_total,
            cases=cases,
            created_at=submission_model.created_at,
            updated_at=submission_model.updated_at,
            exam_attempt_id=str(submission_model.exam_attempt_id) if submission_model.exam_attempt_id else None
        )

    def _to_model(self, submission: Submission) -> SubmissionModel:
        from uuid import UUID
        return SubmissionModel(
            id=submission.id,
            user_id=submission.user_id,
            challenge_id=submission.challenge_id,
            language=submission.language,
            code=submission.code,
            status=submission.status,
            score=submission.score,
            time_ms_total=submission.time_ms_total,
            cases=[self._case_to_dict(case) for case in submission.cases],
            exam_attempt_id=UUID(submission.exam_attempt_id) if submission.exam_attempt_id else None,
            created_at=submission.created_at,
            updated_at=submission.updated_at
        )

    def _case_to_dict(self, case: TestCaseResult) -> dict:
        return {
            "case_id": case.case_id,
            "status": case.status,
            "time_ms": case.time_ms,
            "memory_mb": case.memory_mb,
            "error_message": case.error_message,
            "output": case.output,
            "expected_output": case.expected_output
        }

    def _dict_to_case(self, case_data: dict) -> TestCaseResult:
        return TestCaseResult(
            case_id=case_data["case_id"],
            status=case_data["status"],
            time_ms=case_data["time_ms"],
            memory_mb=case_data.get("memory_mb"),
            error_message=case_data.get("error_message"),
            output=case_data.get("output"),
            expected_output=case_data.get("expected_output")
        )
