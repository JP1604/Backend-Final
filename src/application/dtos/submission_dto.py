from pydantic import BaseModel
from typing import List, Optional
from ...domain.entities.submission import ProgrammingLanguage, SubmissionStatus


class TestCaseResultResponse(BaseModel):
    case_id: int
    status: SubmissionStatus
    time_ms: int
    memory_mb: Optional[int] = None
    error_message: Optional[str] = None


class SubmitSolutionRequest(BaseModel):
    challenge_id: str
    language: ProgrammingLanguage
    code: str


class SubmissionResponse(BaseModel):
    id: str
    user_id: str
    challenge_id: str
    language: ProgrammingLanguage
    code: str
    status: SubmissionStatus
    score: int
    time_ms_total: int
    cases: List[TestCaseResultResponse]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
