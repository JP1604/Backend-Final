"""
Base class for language-specific code executors
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of a test case execution"""
    
    def __init__(
        self,
        case_id: int,
        status: str,
        time_ms: int,
        memory_mb: int = 0,
        output: str = "",
        expected_output: str = "",
        error_message: str = ""
    ):
        self.case_id = case_id
        self.status = status
        self.time_ms = time_ms
        self.memory_mb = memory_mb
        self.output = output
        self.expected_output = expected_output
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "case_id": self.case_id,
            "status": self.status,
            "time_ms": self.time_ms,
            "memory_mb": self.memory_mb,
            "output": self.output,
            "expected_output": self.expected_output,
            "error_message": self.error_message
        }


class BaseExecutor(ABC):
    """Base class for all language executors"""
    
    def __init__(self):
        self.language = self.get_language_name()
        logger.info(f"Initialized {self.language} executor")
    
    @abstractmethod
    def get_language_name(self) -> str:
        """Return the name of the programming language"""
        pass
    
    @abstractmethod
    async def execute_code(
        self,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: int,
        memory_limit: int
    ) -> Dict[str, Any]:
        """
        Execute code against test cases
        
        Args:
            code: Source code to execute
            test_cases: List of test case dictionaries with 'expected_output' (required) and 'input' (optional)
            time_limit: Time limit in milliseconds
            memory_limit: Memory limit in MB
            
        Returns:
            Dictionary containing:
                - status: Overall status (ACCEPTED, WRONG_ANSWER, etc.)
                - score: Score (0-100)
                - total_time_ms: Total execution time
                - cases: List of ExecutionResult objects
        """
        pass
    
    def _calculate_score(self, results: List[ExecutionResult]) -> int:
        """Calculate score based on test case results"""
        if not results:
            return 0
        
        passed = sum(1 for r in results if r.status == "ACCEPTED")
        return int((passed / len(results)) * 100)
    
    def _determine_overall_status(self, results: List[ExecutionResult]) -> str:
        """Determine overall submission status from test results"""
        if not results:
            return "RUNTIME_ERROR"
        
        # Check for compilation errors first
        if any(r.status == "COMPILATION_ERROR" for r in results):
            return "COMPILATION_ERROR"
        
        # Check for runtime errors
        if any(r.status == "RUNTIME_ERROR" for r in results):
            return "RUNTIME_ERROR"
        
        # Check for time limit exceeded
        if any(r.status == "TIME_LIMIT_EXCEEDED" for r in results):
            return "TIME_LIMIT_EXCEEDED"
        
        # Check if all passed
        if all(r.status == "ACCEPTED" for r in results):
            return "ACCEPTED"
        
        # Otherwise, wrong answer
        return "WRONG_ANSWER"
    
    async def validate_code(self, code: str) -> tuple[bool, str]:
        """
        Validate code before execution 
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not code or not code.strip():
            return False, "Code cannot be empty"
        
        if len(code) > 1_000_000:  # 1MB limit
            return False, "Code exceeds maximum size limit"
        
        return True, ""
    
    def _create_error_result(
        self,
        case_id: int,
        status: str,
        error_message: str
    ) -> ExecutionResult:
        """Create an error result for a test case"""
        return ExecutionResult(
            case_id=case_id,
            status=status,
            time_ms=0,
            memory_mb=0,
            error_message=error_message
        )

