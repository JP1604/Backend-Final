"""
Python code executor
Executes Python code and compares output with expected results
"""
import asyncio
import time
import subprocess
import sys
import io
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
        Execute a single test case by actually running the Python code
        
        Args:
            code: Python code to execute
            input_data: Input for the test case
            expected_output: Expected output string
            case_id: Test case identifier
            time_limit: Time limit in milliseconds
            memory_limit: Memory limit in MB (not enforced in this basic implementation)
            
        Returns:
            ExecutionResult with actual execution results
        """
        start_time = time.time()
        actual_output = ""
        error_message = ""
        status = "RUNTIME_ERROR"
        
        try:
            # Prepare the code with input handling
            # Wrap code to capture stdout and handle input
            # Escape single quotes in input data
            escaped_input = input_data.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
            
            wrapped_code = f"""
import sys
from io import StringIO

# Capture stdout
old_stdout = sys.stdout
sys.stdout = StringIO()

# Set stdin to input data
old_stdin = sys.stdin
sys.stdin = StringIO('''{escaped_input}''')

try:
    # User's code
{self._indent_code(code)}
finally:
    # Restore stdout and get output
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    sys.stdin = old_stdin
    print(output, end='')
"""
            
            # Execute code with timeout
            timeout_seconds = (time_limit / 1000.0) + 0.5  # Add small buffer
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-c", wrapped_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB output limit
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution_time = int((time.time() - start_time) * 1000)
                return ExecutionResult(
                    case_id=case_id,
                    status="TIME_LIMIT_EXCEEDED",
                    time_ms=execution_time,
                    memory_mb=0,
                    output="",
                    expected_output=expected_output,
                    error_message=f"Execution exceeded time limit of {time_limit}ms"
                )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Check if process had errors
            if process.returncode != 0:
                error_message = stderr.decode('utf-8', errors='replace') if stderr else "Unknown runtime error"
                actual_output = stdout.decode('utf-8', errors='replace') if stdout else ""
                return ExecutionResult(
                    case_id=case_id,
                    status="RUNTIME_ERROR",
                    time_ms=execution_time,
                    memory_mb=0,
                    output=actual_output,
                    expected_output=expected_output,
                    error_message=error_message
                )
            
            # Get actual output
            actual_output = stdout.decode('utf-8', errors='replace').strip()
            
            # Normalize outputs for comparison (strip whitespace, normalize line endings)
            actual_normalized = self._normalize_output(actual_output)
            expected_normalized = self._normalize_output(expected_output)
            
            # Compare outputs
            if actual_normalized == expected_normalized:
                status = "ACCEPTED"
            else:
                status = "WRONG_ANSWER"
                error_message = f"Expected: '{expected_output}', Got: '{actual_output}'"
            
            # Check time limit
            if execution_time > time_limit:
                status = "TIME_LIMIT_EXCEEDED"
                error_message = f"Execution exceeded time limit of {time_limit}ms"
            
            return ExecutionResult(
                case_id=case_id,
                status=status,
                time_ms=execution_time,
                memory_mb=0,  # Memory tracking not implemented in basic version
                output=actual_output,
                expected_output=expected_output,
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Error executing test case {case_id}: {str(e)}", exc_info=True)
            return ExecutionResult(
                case_id=case_id,
                status="RUNTIME_ERROR",
                time_ms=execution_time,
                memory_mb=0,
                output=actual_output,
                expected_output=expected_output,
                error_message=f"Execution error: {str(e)}"
            )
    
    def _indent_code(self, code: str) -> str:
        """Indent code by 4 spaces for wrapping"""
        if not code:
            return ""
        lines = code.split('\n')
        # Indent each non-empty line, preserve empty lines
        indented = []
        for line in lines:
            if line.strip():
                indented.append('    ' + line)
            else:
                indented.append(line)
        return '\n'.join(indented)
    
    def _normalize_output(self, output: str) -> str:
        """Normalize output for comparison (strip, normalize line endings)"""
        if not output:
            return ""
        # Strip leading/trailing whitespace and normalize line endings
        normalized = output.strip().replace('\r\n', '\n').replace('\r', '\n')
        # Remove trailing newlines for comparison
        return normalized.rstrip('\n')
    
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

