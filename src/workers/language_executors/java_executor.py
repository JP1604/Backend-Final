"""
Java code executor (STUB)
This is a simplified stub that simulates code execution
Replace with proper Docker-based sandboxed execution later
"""
import asyncio
import random
from typing import List, Dict, Any
import logging
from .base_executor import BaseExecutor, ExecutionResult

logger = logging.getLogger(__name__)


class JavaExecutor(BaseExecutor):
    """Executor for Java code submissions"""
    
    def get_language_name(self) -> str:
        return "Java"
    
    async def execute_code(
        self,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: int,
        memory_limit: int
    ) -> Dict[str, Any]:
        """
        Execute Java code against test cases (STUB VERSION)
        
        TODO: Replace with proper Docker container execution:
        - Use openjdk Docker image
        - Compile Java code (javac)
        - Run with JVM memory limits
        - Handle compilation errors
        - Execute with timeout
        """
        logger.info(f"Executing Java code with {len(test_cases)} test cases")
        
        # Validate code
        is_valid, error_msg = await self.validate_code(code)
        if not is_valid:
            return self._create_error_response(error_msg)
        
        # Simulate compilation time
        compilation_time = random.randint(500, 1500)
        await asyncio.sleep(compilation_time / 1000.0)
        
        # Simulate compilation failure (10% chance)
        if random.random() < 0.1:
            return {
                "status": "COMPILATION_ERROR",
                "score": 0,
                "total_time_ms": compilation_time,
                "cases": [],
                "error_message": "Compilation error: class Solution not found (stub)",
                "language": "java"
            }
        
        results = []
        total_time = compilation_time
        
        for i, test_case in enumerate(test_cases):
            case_id = test_case.get("id", i + 1)
            input_data = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            
            result = await self._execute_test_case(
                code, input_data, expected_output, case_id, time_limit, memory_limit
            )
            
            results.append(result)
            total_time += result.time_ms
        
        status = self._determine_overall_status(results)
        score = self._calculate_score(results)
        
        return {
            "status": status,
            "score": score,
            "total_time_ms": total_time,
            "cases": [r.to_dict() for r in results],
            "language": "java"
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
        """Execute a single Java test case (STUB)"""
        
        # Java typically slower than Python due to JVM startup
        execution_time = random.randint(200, 800)
        await asyncio.sleep(execution_time / 1000.0)
        
        outcome = random.choices(
            ["ACCEPTED", "WRONG_ANSWER", "RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED"],
            weights=[75, 15, 5, 5]
        )[0]
        
        if execution_time > time_limit:
            outcome = "TIME_LIMIT_EXCEEDED"
        
        memory_used = random.randint(50, 150)  # Java uses more memory
        
        if outcome == "ACCEPTED":
            return ExecutionResult(
                case_id=case_id,
                status="ACCEPTED",
                time_ms=execution_time,
                memory_mb=memory_used,
                output=expected_output,
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
        else:
            return ExecutionResult(
                case_id=case_id,
                status="RUNTIME_ERROR",
                time_ms=execution_time,
                memory_mb=memory_used,
                error_message="Runtime error: NullPointerException (stub)"
            )
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "status": "COMPILATION_ERROR",
            "score": 0,
            "total_time_ms": 0,
            "cases": [],
            "error_message": error_message,
            "language": "java"
        }
    
    async def validate_code(self, code: str) -> tuple[bool, str]:
        """Validate Java code"""
        is_valid, error = await super().validate_code(code)
        if not is_valid:
            return is_valid, error
        
        # Java-specific validation
        if "class Solution" not in code and "public class" not in code:
            logger.warning("Java code should contain a class definition")
        
        return True, ""

