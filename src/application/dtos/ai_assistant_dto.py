"""
DTOs for AI Assistant functionality
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class TestCaseGenerationDTO(BaseModel):
    """DTO for a generated test case"""
    input: str = Field(..., description="Input data for the test case")
    expected_output: str = Field(..., description="Expected output for the test case")
    is_hidden: bool = Field(default=False, description="Whether this test case is hidden from students")
    order_index: int = Field(default=1, description="Order index for test case execution")


class ExampleDTO(BaseModel):
    """DTO for a challenge example"""
    input: str = Field(..., description="Example input")
    output: str = Field(..., description="Example output")
    explanation: str = Field(..., description="Explanation of why this is the correct output")


class ChallengeLimitsDTO(BaseModel):
    """DTO for challenge execution limits"""
    timeLimitMs: int = Field(default=1500, description="Time limit in milliseconds")
    memoryLimitMb: int = Field(default=256, description="Memory limit in megabytes")


class GenerateChallengeRequest(BaseModel):
    """Request DTO for generating a challenge suggestion"""
    topic: str = Field(..., min_length=3, max_length=200, description="Topic or category for the challenge")
    language: Optional[str] = Field(None, description="Preferred programming language (python, java, nodejs, cpp)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Binary Trees",
                "language": "python"
            }
        }


class GenerateChallengeResponse(BaseModel):
    """Response DTO for a generated challenge suggestion"""
    title: str = Field(..., max_length=200, description="Challenge title")
    description: str = Field(..., description="Full challenge description with sections")
    difficulty: str = Field(..., description="Challenge difficulty: Easy, Medium, or Hard")
    tags: List[str] = Field(..., min_length=1, max_length=10, description="List of relevant tags")
    examples: List[ExampleDTO] = Field(..., min_length=1, description="List of examples with explanations")
    testCases: List[TestCaseGenerationDTO] = Field(..., min_length=5, description="List of test cases")
    limits: ChallengeLimitsDTO = Field(..., description="Execution time and memory limits")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Find Maximum Depth of Binary Tree",
                "description": "**Descripción:**\nDado un árbol binario, encuentra la profundidad máxima...",
                "difficulty": "Easy",
                "tags": ["binary-tree", "recursion", "depth-first-search"],
                "examples": [
                    {
                        "input": "3\n1 2 3",
                        "output": "2",
                        "explanation": "El árbol tiene profundidad 2"
                    }
                ],
                "testCases": [
                    {
                        "input": "1\n5",
                        "expected_output": "1",
                        "is_hidden": False,
                        "order_index": 1
                    }
                ],
                "limits": {
                    "timeLimitMs": 1500,
                    "memoryLimitMb": 256
                }
            }
        }


class AIAssistantHealthResponse(BaseModel):
    """Response for AI Assistant health check"""
    status: str = Field(..., description="Service status")
    openai_configured: bool = Field(..., description="Whether OpenAI API is configured")
    model: str = Field(..., description="OpenAI model being used")


class ValidateTestCasesRequest(BaseModel):
    """Request DTO for validating test cases with solution code"""
    solution_code: str = Field(..., min_length=1, description="Solution code to validate test cases")
    language: str = Field(..., description="Programming language (python, java, nodejs, cpp)")
    test_cases: List[TestCaseGenerationDTO] = Field(..., min_length=1, description="Test cases to validate")
    time_limit_ms: int = Field(default=5000, description="Time limit for execution in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "solution_code": "def solution():\n    n = int(input())\n    print(n * 2)",
                "language": "python",
                "test_cases": [
                    {
                        "input": "5",
                        "expected_output": "10",
                        "is_hidden": False,
                        "order_index": 1
                    }
                ],
                "time_limit_ms": 5000
            }
        }


class TestCaseValidationResult(BaseModel):
    """Result of validating a single test case"""
    order_index: int = Field(..., description="Test case order")
    input: str = Field(..., description="Test case input")
    expected_output: str = Field(..., description="Expected output from AI")
    actual_output: Optional[str] = Field(None, description="Actual output from code execution")
    passed: bool = Field(..., description="Whether test case passed")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")


class ValidateTestCasesResponse(BaseModel):
    """Response DTO for test cases validation"""
    total_test_cases: int = Field(..., description="Total number of test cases")
    passed_count: int = Field(..., description="Number of test cases that passed")
    failed_count: int = Field(..., description="Number of test cases that failed")
    validation_results: List[TestCaseValidationResult] = Field(..., description="Detailed results for each test case")
    all_passed: bool = Field(..., description="Whether all test cases passed")
    recommendation: str = Field(..., description="Recommendation for the instructor")

