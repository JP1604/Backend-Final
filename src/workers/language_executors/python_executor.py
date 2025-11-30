"""
Python code executor using Docker
Executes Python code in isolated Docker containers
"""
import logging
from typing import List, Dict, Any, Optional
from .base_executor import BaseExecutor, ExecutionResult
from .docker_runner import DockerRunner

logger = logging.getLogger(__name__)


class PythonExecutor(BaseExecutor):
    """Executor for Python code submissions using Docker"""
    
    def __init__(self, docker_runner: Optional[DockerRunner] = None):
        """
        Initialize Python executor
        
        Args:
            docker_runner: Optional DockerRunner instance (creates new one if not provided)
        """
        super().__init__()
        self.docker_runner = docker_runner or DockerRunner()
    
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
        Execute Python code against test cases using Docker
        """
        code_preview = code[:200] + "..." if len(code) > 200 else code
        logger.info(
            f"[PYTHON_EXEC] Starting execution - Test cases: {len(test_cases)}, "
            f"Time limit: {time_limit}ms, Memory limit: {memory_limit}MB"
        )
        logger.debug(f"[PYTHON_EXEC] Code preview (first 200 chars): {code_preview}")
        
        # Validate code first
        is_valid, error_msg = await self.validate_code(code)
        if not is_valid:
            logger.warning(f"[PYTHON_EXEC] Code validation failed: {error_msg}")
            return self._create_error_response(error_msg)
        
        results = []
        total_time = 0
        
        # Execute each test case
        for i, test_case in enumerate(test_cases):
            case_id = test_case.get("id", i + 1)
            input_data = test_case.get("input", "") or ""
            expected_output = test_case.get("expected_output", "")
            
            logger.info(
                f"[PYTHON_EXEC] Executing test case {case_id} - "
                f"Input: {repr(input_data[:100])}, Expected: {repr(expected_output[:100])}"
            )
            
            result = await self._execute_test_case(
                code, input_data, expected_output, case_id, time_limit, memory_limit
            )
            
            logger.info(
                f"[PYTHON_EXEC] Test case {case_id} completed - "
                f"Status: {result.status}, Time: {result.time_ms}ms, "
                f"Actual output: {repr(result.output[:100])}, "
                f"Error: {repr(result.error_message[:100]) if result.error_message else 'None'}"
            )
            
            results.append(result)
            total_time += result.time_ms
        
        # Calculate final status and score
        status = self._determine_overall_status(results)
        score = self._calculate_score(results)
        
        logger.info(
            f"[PYTHON_EXEC] Execution completed - "
            f"Status: {status}, Score: {score}, Total time: {total_time}ms, "
            f"Passed: {sum(1 for r in results if r.status == 'ACCEPTED')}/{len(results)}"
        )
        
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
        """Execute a single test case using Docker"""
        
        try:
            # Run code in Docker container
            docker_result = await self.docker_runner.run_code(
                language="python",
                code=code,
                input_data=input_data,
                time_limit_ms=time_limit,
                memory_limit_mb=memory_limit,
                compile_first=False
            )
            
            actual_output = docker_result.get("output", "").strip()
            error_output = docker_result.get("error", "").strip()
            execution_time = docker_result.get("execution_time_ms", 0)
            exit_code = docker_result.get("exit_code", 1)
            
            logger.debug(
                f"[PYTHON_EXEC] Docker result for case {case_id} - "
                f"Exit code: {exit_code}, Time: {execution_time}ms, "
                f"Output length: {len(actual_output)}, Error length: {len(error_output)}"
            )
            
            # Filter out debug output from stderr
            actual_error = "\n".join([
                line for line in error_output.split("\n")
                if not line.strip().startswith("Files in") 
                and not line.strip().startswith("---Running command---")
                and not line.strip().startswith("total")
                and not line.strip().startswith("drwx")
                and line.strip()
            ])
            
            # Normalize outputs for comparison
            actual_normalized = self._normalize_output(actual_output)
            expected_normalized = self._normalize_output(expected_output)
            
            # Determine status
            if execution_time > time_limit:
                status = "TIME_LIMIT_EXCEEDED"
                error_message = f"Execution exceeded time limit of {time_limit}ms"
            elif exit_code != 0:
                status = "RUNTIME_ERROR"
                error_message = actual_error or "Runtime error occurred"
            elif actual_normalized == expected_normalized:
                status = "ACCEPTED"
                error_message = ""
            else:
                status = "WRONG_ANSWER"
                error_message = "Output does not match expected result"
                logger.debug(
                    f"[PYTHON_EXEC] Output mismatch for case {case_id} - "
                    f"Expected: {repr(expected_normalized)}, Got: {repr(actual_normalized)}"
                )
            
            return ExecutionResult(
                case_id=case_id,
                status=status,
                time_ms=execution_time,
                memory_mb=docker_result.get("memory_used_mb", 0),
                output=actual_output,
                expected_output=expected_output,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Error executing test case {case_id}: {str(e)}", exc_info=True)
            return ExecutionResult(
                case_id=case_id,
                status="RUNTIME_ERROR",
                time_ms=0,
                memory_mb=0,
                error_message=f"Execution error: {str(e)}"
            )
    
    def _normalize_output(self, output: str) -> str:
        """Normalize output for comparison (trim, handle line endings)"""
        return output.strip().replace('\r\n', '\n').replace('\r', '\n')
    
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
        
        # Python-specific validation
        dangerous_imports = ["os", "sys", "subprocess", "socket", "shutil"]
        for imp in dangerous_imports:
            if f"import {imp}" in code or f"from {imp}" in code:
                return False, f"Dangerous import detected: {imp}. This is not allowed for security reasons."
        
        return True, ""
