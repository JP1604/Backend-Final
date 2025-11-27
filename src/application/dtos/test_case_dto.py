from pydantic import BaseModel
from typing import Optional


class CreateTestCaseRequest(BaseModel):
    """Request to create a test case for a challenge"""
    input: str
    expected_output: str
    is_hidden: bool = False
    order_index: int = 1


class TestCaseResponse(BaseModel):
    """Response with test case details"""
    id: str
    challenge_id: str
    input: str
    expected_output: str
    is_hidden: bool
    order_index: int

