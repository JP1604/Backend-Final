from enum import Enum
from datetime import datetime
from typing import List, Optional


class SubmissionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    COMPILATION_ERROR = "COMPILATION_ERROR"


class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    CPP = "cpp"
    JAVA = "java"


class TestCaseResult:
    def __init__(
        self,
        case_id: int,
        status: SubmissionStatus,
        time_ms: int,
        memory_mb: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        self.case_id = case_id
        self.status = status
        self.time_ms = time_ms
        self.memory_mb = memory_mb
        self.error_message = error_message


class Submission:
    def __init__(
        self,
        id: str,
        user_id: str,
        challenge_id: str,
        language: ProgrammingLanguage,
        code: str,
        status: SubmissionStatus,
        score: int,
        time_ms_total: int,
        cases: List[TestCaseResult],
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.language = language
        self.code = code
        self.status = status
        self.score = score
        self.time_ms_total = time_ms_total
        self.cases = cases
        self.created_at = created_at
        self.updated_at = updated_at

    def is_completed(self) -> bool:
        return self.status in [
            SubmissionStatus.ACCEPTED,
            SubmissionStatus.WRONG_ANSWER,
            SubmissionStatus.TIME_LIMIT_EXCEEDED,
            SubmissionStatus.RUNTIME_ERROR,
            SubmissionStatus.COMPILATION_ERROR
        ]

    def is_successful(self) -> bool:
        return self.status == SubmissionStatus.ACCEPTED

    def is_processing(self) -> bool:
        return self.status in [SubmissionStatus.QUEUED, SubmissionStatus.RUNNING]
