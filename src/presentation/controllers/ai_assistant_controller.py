"""
AI Assistant Controller
Handles HTTP requests for AI-powered challenge generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
import os

from application.dtos.ai_assistant_dto import (
    GenerateChallengeRequest,
    GenerateChallengeResponse,
    AIAssistantHealthResponse,
    ValidateTestCasesRequest,
    ValidateTestCasesResponse
)
from application.use_cases.ai.generate_challenge_use_case import GenerateChallengeUseCase
from application.use_cases.ai.validate_test_cases_use_case import ValidateTestCasesUseCase
from infrastructure.services.openai_service import OpenAIService
from workers.redis_queue_service import RedisQueueService
from presentation.middleware.auth_middleware import get_current_user
from domain.entities.user import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["ai-assistant"],
    responses={404: {"description": "Not found"}}
)


def _build_openai_service() -> OpenAIService:
    """Factory for OpenAI service"""
    return OpenAIService()


def _build_generate_challenge_use_case(openai_service: OpenAIService) -> GenerateChallengeUseCase:
    """Factory for generate challenge use case"""
    return GenerateChallengeUseCase(openai_service)


def _build_queue_service() -> RedisQueueService:
    """Factory for Redis queue service"""
    return RedisQueueService()


def _build_validate_test_cases_use_case(queue_service: RedisQueueService) -> ValidateTestCasesUseCase:
    """Factory for validate test cases use case"""
    return ValidateTestCasesUseCase(queue_service)


@router.get(
    "/health",
    response_model=AIAssistantHealthResponse,
    summary="Check AI Assistant service health"
)
async def check_health():
    """
    Check if AI Assistant service is properly configured and available.
    
    Returns:
        Service health status including OpenAI configuration
    """
    openai_service = _build_openai_service()
    
    return AIAssistantHealthResponse(
        status="healthy" if openai_service.api_key else "unconfigured",
        openai_configured=bool(openai_service.api_key),
        model=openai_service.model
    )


@router.post(
    "/generate-challenge",
    response_model=GenerateChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a challenge suggestion using AI"
)
async def generate_challenge(
    request: GenerateChallengeRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate a programming challenge suggestion based on a topic using AI.
    
    **Only professors and admins can use this endpoint.**
    
    The AI assistant will:
    - Generate a challenge title and full description
    - Propose difficulty level and relevant tags
    - Create example inputs/outputs with explanations
    - Generate test cases (public and hidden) for validation
    - Suggest execution time and memory limits
    
    **Important:** All AI-generated content should be reviewed and validated
    by the instructor before publishing to students.
    
    Args:
        request: Contains topic and optional language preference
        current_user: Authenticated user (from JWT token)
        
    Returns:
        Complete challenge suggestion with test cases
        
    Raises:
        403: If user is not a professor or admin
        400: If request validation fails
        500: If OpenAI API fails
    """
    # Verify user has permission (only professors and admins)
    user_role = UserRole(current_user["role"])
    if user_role not in [UserRole.PROFESSOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors and administrators can generate challenge suggestions"
        )
    
    logger.info(
        f"[AI_GENERATE_CHALLENGE] User {current_user['email']} requesting challenge "
        f"for topic: '{request.topic}' (language: {request.language})"
    )
    
    try:
        # Build services and use case
        openai_service = _build_openai_service()
        use_case = _build_generate_challenge_use_case(openai_service)
        
        # Generate challenge suggestion
        suggestion = await use_case.execute(
            topic=request.topic,
            language=request.language
        )
        
        logger.info(
            f"[AI_GENERATE_CHALLENGE] Successfully generated challenge: '{suggestion['title']}' "
            f"for user {current_user['email']}"
        )
        
        return GenerateChallengeResponse(**suggestion)
        
    except ValueError as e:
        # Validation errors (bad input or missing config)
        logger.warning(f"Validation error in AI generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors (API failures, network issues, etc.)
        logger.error(f"Error generating challenge with AI: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate challenge suggestion: {str(e)}"
        )


@router.get(
    "/info",
    summary="Get AI Assistant information and capabilities"
)
async def get_assistant_info(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get information about the AI Assistant capabilities.
    
    Returns:
        Information about what the AI Assistant can do
    """
    user_role = UserRole(current_user["role"])
    
    return {
        "name": "AI Challenge Assistant",
        "version": "1.0.0",
        "description": (
            "AI-powered assistant to help professors and administrators create "
            "programming challenges for the online judge platform."
        ),
        "capabilities": [
            "Generate challenge ideas based on topics or categories",
            "Create detailed problem descriptions with input/output specifications",
            "Propose example test cases with explanations",
            "Generate hidden test cases for comprehensive evaluation",
            "Suggest difficulty levels and relevant tags",
            "Recommend execution time and memory limits"
        ],
        "supported_languages": ["Python", "Java", "Node.js", "C++"],
        "access": "Professor and Admin only",
        "user_has_access": user_role in [UserRole.PROFESSOR, UserRole.ADMIN],
        "notes": [
            "AI-generated content should always be reviewed by instructors",
            "Test cases must be validated before publishing",
            "The AI does not evaluate code, only generates challenge content"
        ]
    }


@router.post(
    "/validate-test-cases",
    response_model=ValidateTestCasesResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate AI-generated test cases by executing solution code"
)
async def validate_test_cases(
    request: ValidateTestCasesRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Validate test cases by executing solution code against them.
    
    **Only professors and admins can use this endpoint.**
    
    This endpoint helps verify that AI-generated test cases produce the correct
    expected outputs by running actual solution code. This is critical before
    publishing challenges to students.
    
    The validation process:
    - Submits solution code to the execution worker system
    - Runs code against each test case input
    - Compares actual output with expected output
    - Reports which test cases passed and which failed
    - Provides detailed results including execution times
    
    Args:
        request: Contains solution code, language, test cases, and time limit
        current_user: Authenticated user (from JWT token)
        
    Returns:
        Validation results showing passed/failed test cases with details
        
    Raises:
        403: If user is not a professor or admin
        400: If request validation fails
        500: If execution system fails
    """
    # Verify user has permission (only professors and admins)
    user_role = UserRole(current_user["role"])
    if user_role not in [UserRole.PROFESSOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors and administrators can validate test cases"
        )
    
    logger.info(
        f"[AI_VALIDATE_TESTS] User {current_user['email']} validating "
        f"{len(request.test_cases)} test cases for {request.language}"
    )
    
    try:
        # Build services and use case
        queue_service = _build_queue_service()
        use_case = _build_validate_test_cases_use_case(queue_service)
        
        # Validate test cases
        result = await use_case.execute(
            solution_code=request.solution_code,
            language=request.language,
            test_cases=[tc.dict() for tc in request.test_cases],
            time_limit_ms=request.time_limit_ms
        )
        
        logger.info(
            f"[AI_VALIDATE_TESTS] Validation complete for user {current_user['email']}: "
            f"{result['passed_count']}/{result['total_test_cases']} passed"
        )
        
        return ValidateTestCasesResponse(**result)
        
    except ValueError as e:
        # Validation errors (bad input)
        logger.warning(f"Validation error in test case validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors (execution system failures, etc.)
        logger.error(f"Error validating test cases: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate test cases: {str(e)}"
        )
