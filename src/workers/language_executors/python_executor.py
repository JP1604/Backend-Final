"""
Python code executor (STUB)
This is a simplified stub that simulates code execution
Replace with proper Docker-based sandboxed execution later
"""
import asyncio
import time
import random
from typing import List, Dict, Any
import logging
from .base_executor import BaseExecutor, ExecutionResult

logger = logging.getLogger(__name__)


class PythonExecutor(BaseExecutor):
    """Executor for Python code submissions"""
    
    def get_language_name(self) -> str:
        return "Python"
    
    async def execute_code(
        self,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: int,
        memory_limit: int
    ) -> Dict[str, Any]:
        """
        Execute Python code against test cases (STUB VERSION)
        
        TODO: Replace with proper Docker container execution:
        """
        logger.info(f"Executing Python code with {len(test_cases)} test cases")
        
        # Validate code first
        is_valid, error_msg = await self.validate_code(code)
        if not is_valid:
            return self._create_error_response(error_msg)
        
        results = []
        total_time = 0
        
        # Simulate execution for each test case
        for i, test_case in enumerate(test_cases):
            case_id = test_case.get("id", i + 1)
            input_data = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            
            # STUB: Simulate code execution
            result = await self._execute_test_case(
                code, input_data, expected_output, case_id, time_limit, memory_limit
            )
            
            results.append(result)
            total_time += result.time_ms
        
        # Calculate final status and score
        status = self._determine_overall_status(results)
        score = self._calculate_score(results)
        
        return {
            "status": status,
            "score": score,
            "total_time_ms": total_time,
            "cases": [r.to_dict() for r in results],
            "language": "python"
        }
    
    async def _execute_test_case(
        self,
        code: str,
        input_data: str,
        expected_output: str,
        case_id: int,
        time_limit: int,
        memory_limit: int
    ) -> ExecutionResult:
        """
        Execute a single test case (STUB)
        
        TODO: Actual implementation should:
        1. Create isolated Docker container
        2. Mount code and input files
        3. Run with timeout and memory limits
        4. Capture stdout/stderr
        5. Compare output with expected
        6. Return ExecutionResult with actual metrics
        """
        
        # Simulate execution time (100-500ms)
        execution_time = random.randint(100, 500)
        await asyncio.sleep(execution_time / 1000.0)  # Simulate work
        
        # Simple validation: check if code contains basic patterns
        # In a real implementation, this would actually execute the code
        code_lower = code.lower()
        has_return = "return" in code_lower or "print" in code_lower
        
        # Determine outcome based on simple heuristics
        # For stub: if code looks valid and has basic structure, accept it
        if has_return and len(code.strip()) > 10:
            # 90% chance of acceptance for valid-looking code
            outcome = random.choices(
                ["ACCEPTED", "WRONG_ANSWER"],
                weights=[90, 10]
            )[0]
        else:
            # Invalid code structure
            outcome = "RUNTIME_ERROR"
        
        # Check for time limit
        if execution_time > time_limit:
            outcome = "TIME_LIMIT_EXCEEDED"
        
        # Simulate memory usage (10-50MB)
        memory_used = random.randint(10, 50)
        
        if outcome == "ACCEPTED":
            return ExecutionResult(
                case_id=case_id,
                status="ACCEPTED",
                time_ms=execution_time,
                memory_mb=memory_used,
                output=expected_output,  # Stub: assume correct output
                expected_output=expected_output
            )
        elif outcome == "WRONG_ANSWER":
            return ExecutionResult(
                case_id=case_id,
                status="WRONG_ANSWER",
                time_ms=execution_time,
                memory_mb=memory_used,
                output="Wrong output",
                expected_output=expected_output,
                error_message="Output does not match expected result"
            )
        elif outcome == "TIME_LIMIT_EXCEEDED":
            return ExecutionResult(
                case_id=case_id,
                status="TIME_LIMIT_EXCEEDED",
                time_ms=time_limit + 100,
                memory_mb=memory_used,
                error_message=f"Execution exceeded time limit of {time_limit}ms"
            )
        else:  # RUNTIME_ERROR
            return ExecutionResult(
                case_id=case_id,
                status="RUNTIME_ERROR",
                time_ms=execution_time,
                memory_mb=memory_used,
                error_message="Runtime error: Invalid code structure"
            )
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "status": "COMPILATION_ERROR",
            "score": 0,
            "total_time_ms": 0,
            "cases": [],
            "error_message": error_message,
            "language": "python"
        }
    
    async def validate_code(self, code: str) -> tuple[bool, str]:
        """Validate Python code"""
        is_valid, error = await super().validate_code(code)
        if not is_valid:
            return is_valid, error
        
        # Additional Python-specific validation
        dangerous_imports = ["os", "sys", "subprocess", "socket"]
        for imp in dangerous_imports:
            if f"import {imp}" in code:
                logger.warning(f"Dangerous import detected: {imp}")
                # In production, this should reject the code
                # For stub, we just log it
        
        return True, ""

