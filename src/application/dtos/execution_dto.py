"""
DTOs for code execution and submission processing
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TestCaseDTO:
    """Test case data transfer object"""
    id: str
    expected_output: str
    input: Optional[str] = None
    is_hidden: bool = False
    order_index: int = 0


@dataclass
class SubmissionJobDTO:
    """Job data for submission processing"""
    submission_id: str
    challenge_id: str
    user_id: str
    language: str
    code: str
    test_cases: List[TestCaseDTO]
    enqueued_at: datetime


@dataclass
class TestCaseResultDTO:
    """Result of a single test case execution"""
    case_id: int
    status: str  # ACCEPTED, WRONG_ANSWER, etc.
    time_ms: int
    memory_mb: int
    output: Optional[str] = None
    expected_output: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionResultDTO:
    """Result of code execution"""
    submission_id: str
    status: str  # Overall status
    score: int  # 0-100
    total_time_ms: int
    cases: List[TestCaseResultDTO]
    language: str
    error_message: Optional[str] = None


@dataclass
class EnqueueSubmissionDTO:
    """Request to enqueue a submission for execution"""
    submission_id: str
    challenge_id: str
    user_id: str
    language: str
    code: str


@dataclass
class SubmissionStatusDTO:
    """Current status of a submission"""
    submission_id: str
    status: str
    score: Optional[int] = None
    total_time_ms: Optional[int] = None
    updated_at: Optional[datetime] = None

