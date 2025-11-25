"""
NodeJS code executor (STUB)
This is a simplified stub that simulates code execution
Replace with proper Docker-based sandboxed execution later
"""
import asyncio
import random
from typing import List, Dict, Any
import logging
from .base_executor import BaseExecutor, ExecutionResult

logger = logging.getLogger(__name__)


class NodeJSExecutor(BaseExecutor):
    """Executor for NodeJS/JavaScript code submissions"""
    
    def get_language_name(self) -> str:
        return "NodeJS"
    
    async def execute_code(
        self,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: int,
        memory_limit: int
    ) -> Dict[str, Any]:
        """
        Execute NodeJS code against test cases (STUB VERSION)
        
        TODO: Replace with proper Docker container execution:
        """
        logger.info(f"Executing NodeJS code with {len(test_cases)} test cases")
        
        # Validate code
        is_valid, error_msg = await self.validate_code(code)
        if not is_valid:
            return self._create_error_response(error_msg)
        
        results = []
        total_time = 0
        
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
            "language": "nodejs"
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
        """Execute a single NodeJS test case (STUB)"""
        
        # NodeJS is generally fast
        execution_time = random.randint(80, 400)
        await asyncio.sleep(execution_time / 1000.0)
        
        outcome = random.choices(
            ["ACCEPTED", "WRONG_ANSWER", "RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED"],
            weights=[80, 12, 5, 3]
        )[0]
        
        if execution_time > time_limit:
            outcome = "TIME_LIMIT_EXCEEDED"
        
        memory_used = random.randint(20, 80)
        
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
                error_message="Runtime error: TypeError: Cannot read property (stub)"
            )
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "status": "COMPILATION_ERROR",
            "score": 0,
            "total_time_ms": 0,
            "cases": [],
            "error_message": error_message,
            "language": "nodejs"
        }
    
    async def validate_code(self, code: str) -> tuple[bool, str]:
        """Validate NodeJS code"""
        is_valid, error = await super().validate_code(code)
        if not is_valid:
            return is_valid, error
        
        # NodeJS-specific validation
        dangerous_modules = ["fs", "child_process", "net", "http"]
        for module in dangerous_modules:
            if f"require('{module}')" in code or f'require("{module}")' in code:
                logger.warning(f"Dangerous module detected: {module}")
        
        return True, ""

