"""
Use case for validating AI-generated test cases by executing solution code
"""
import logging
import uuid
import asyncio
from typing import List, Dict, Any

from workers.redis_queue_service import RedisQueueService

logger = logging.getLogger(__name__)


class ValidateTestCasesUseCase:
    """
    Use case for validating test cases by executing solution code against them.
    
    This ensures that AI-generated test cases produce the expected outputs
    by running actual code, rather than just trusting the AI's suggestions.
    """
    
    def __init__(self, queue_service: RedisQueueService):
        """
        Initialize the use case with required service.
        
        Args:
            queue_service: Redis queue service for submitting code to workers
        """
        self.queue_service = queue_service
    
    async def execute(
        self,
        solution_code: str,
        language: str,
        test_cases: List[Dict[str, Any]],
        time_limit_ms: int = 5000
    ) -> Dict[str, Any]:
        """
        Validate test cases by executing solution code against them.
        
        Args:
            solution_code: The solution code to execute
            language: Programming language (python, java, nodejs, cpp)
            test_cases: List of test cases with input and expected_output
            time_limit_ms: Time limit for execution in milliseconds
            
        Returns:
            Dictionary containing validation results for each test case
            
        Raises:
            ValueError: If parameters are invalid
            Exception: If validation process fails
        """
        # Validate inputs
        if not solution_code or not solution_code.strip():
            raise ValueError("Solution code cannot be empty")
        
        valid_languages = ["python", "java", "nodejs", "cpp"]
        language = language.lower()
        if language not in valid_languages:
            raise ValueError(
                f"Invalid language '{language}'. Must be one of: {', '.join(valid_languages)}"
            )
        
        if not test_cases or len(test_cases) == 0:
            raise ValueError("At least one test case is required")
        
        logger.info(
            f"Validating {len(test_cases)} test cases for {language} solution"
        )
        
        validation_results = []
        passed_count = 0
        failed_count = 0
        
        # Execute solution against each test case
        for idx, test_case in enumerate(test_cases, 1):
            test_input = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            order_index = test_case.get("order_index", idx)
            
            logger.debug(f"Validating test case {order_index}")
            
            try:
                # Submit code for execution
                submission_id = str(uuid.uuid4())
                
                # Format test case for worker
                test_case_for_worker = [{
                    "id": str(uuid.uuid4()),
                    "input": test_input,
                    "expected_output": expected_output,
                    "is_hidden": False,
                    "order_index": order_index
                }]
                
                print(f"[DEBUG] About to enqueue submission {submission_id} for language {language}")
                logger.info(f"[VALIDATION] Enqueueing submission {submission_id} for test case {order_index}")
                enqueue_result = self.queue_service.enqueue_submission(
                    submission_id=submission_id,
                    challenge_id="validation",  # Dummy challenge ID for validation
                    user_id="system",  # System user for validation
                    language=language,
                    code=solution_code,
                    test_cases=test_case_for_worker
                )
                print(f"[DEBUG] Enqueue result: {enqueue_result}")
                logger.info(f"[VALIDATION] Enqueue result for {submission_id}: {enqueue_result}")
                
                # Wait for execution with timeout
                max_wait_time = (time_limit_ms / 1000) + 5  # Add 5 seconds buffer
                result = await self._wait_for_result(
                    submission_id,
                    timeout=max_wait_time
                )
                
                if result:
                    # Get execution result from result data
                    status = result.get("status", "ERROR")
                    
                    if status == "COMPLETED":
                        # Get first test case result (we only sent one)
                        test_results = result.get("test_results", [])
                        if test_results and len(test_results) > 0:
                            test_result = test_results[0]
                            actual_output = test_result.get("actual_output", "").strip()
                            expected_output_clean = expected_output.strip()
                            execution_time = test_result.get("execution_time", 0)
                            
                            # Compare outputs
                            passed = actual_output == expected_output_clean
                            
                            if passed:
                                passed_count += 1
                            else:
                                failed_count += 1
                            
                            validation_results.append({
                                "order_index": order_index,
                                "input": test_input,
                                "expected_output": expected_output_clean,
                                "actual_output": actual_output,
                                "passed": passed,
                                "error": test_result.get("error"),
                                "execution_time_ms": int(execution_time * 1000) if execution_time else None
                            })
                        else:
                            # No test results
                            failed_count += 1
                            validation_results.append({
                                "order_index": order_index,
                                "input": test_input,
                                "expected_output": expected_output.strip(),
                                "actual_output": None,
                                "passed": False,
                                "error": "No test results returned",
                                "execution_time_ms": None
                            })
                    else:
                        # Execution failed
                        error_msg = result.get("error", "Execution failed")
                        failed_count += 1
                        validation_results.append({
                            "order_index": order_index,
                            "input": test_input,
                            "expected_output": expected_output.strip(),
                            "actual_output": None,
                            "passed": False,
                            "error": error_msg,
                            "execution_time_ms": None
                        })
                else:
                    # Execution timed out or failed
                    failed_count += 1
                    validation_results.append({
                        "order_index": order_index,
                        "input": test_input,
                        "expected_output": expected_output.strip(),
                        "actual_output": None,
                        "passed": False,
                        "error": "Execution timed out or failed to complete",
                        "execution_time_ms": None
                    })
                    
            except Exception as e:
                logger.error(f"Error validating test case {order_index}: {str(e)}")
                failed_count += 1
                validation_results.append({
                    "order_index": order_index,
                    "input": test_input,
                    "expected_output": expected_output.strip(),
                    "actual_output": None,
                    "passed": False,
                    "error": f"Validation error: {str(e)}",
                    "execution_time_ms": None
                })
        
        # Generate recommendation
        all_passed = failed_count == 0
        if all_passed:
            recommendation = (
                "✅ All test cases passed! The expected outputs match the actual outputs. "
                "These test cases are validated and ready to be published."
            )
        elif passed_count > 0:
            recommendation = (
                f"⚠️ {passed_count} test case(s) passed but {failed_count} failed. "
                "Review the failed test cases and adjust either the solution code or the expected outputs "
                "before publishing."
            )
        else:
            recommendation = (
                "❌ All test cases failed. The solution code may be incorrect or the test cases "
                "need to be reviewed. Please verify both before publishing."
            )
        
        logger.info(
            f"Validation complete: {passed_count} passed, {failed_count} failed"
        )
        
        return {
            "total_test_cases": len(test_cases),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "validation_results": validation_results,
            "all_passed": all_passed,
            "recommendation": recommendation
        }
    
    async def _wait_for_result(
        self,
        submission_id: str,
        timeout: float = 10.0,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Wait for execution result with timeout.
        
        Args:
            submission_id: ID of the submission
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check for results in seconds
            
        Returns:
            Execution result or None if timed out
        """
        elapsed = 0.0
        
        while elapsed < timeout:
            # Check if result is available
            result = await self.queue_service.get_submission_result(submission_id)
            
            if result:
                return result
            
            # Wait before checking again
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        logger.warning(f"Timed out waiting for result of submission {submission_id}")
        return None
