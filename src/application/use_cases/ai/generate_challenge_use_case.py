"""
Use case for generating challenge suggestions using AI
"""
import logging
from typing import Dict, Any, Optional

from infrastructure.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class GenerateChallengeUseCase:
    """
    Use case for generating programming challenge suggestions using AI.
    
    This use case coordinates the interaction with the OpenAI service
    to generate challenge ideas, descriptions, and test cases based on
    a given topic or category.
    """
    
    def __init__(self, openai_service: OpenAIService):
        """
        Initialize the use case with required service.
        
        Args:
            openai_service: Service for interacting with OpenAI API
        """
        self.openai_service = openai_service
    
    async def execute(self, topic: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a challenge suggestion based on the given topic.
        
        Args:
            topic: The topic or category for the challenge (e.g., "Binary Trees")
            language: Optional preferred programming language
            
        Returns:
            Dictionary containing the generated challenge with:
            - title: Challenge title
            - description: Full problem description
            - difficulty: Easy, Medium, or Hard
            - tags: List of relevant tags
            - examples: List of example inputs/outputs with explanations
            - testCases: List of test cases with expected outputs
            - limits: Time and memory limits
            
        Raises:
            ValueError: If topic is empty or OpenAI is not configured
            Exception: If generation fails
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        topic = topic.strip()
        
        # Validate language if provided
        valid_languages = ["python", "java", "nodejs", "cpp"]
        if language:
            language = language.lower()
            if language not in valid_languages:
                raise ValueError(
                    f"Invalid language '{language}'. Must be one of: {', '.join(valid_languages)}"
                )
        
        logger.info(f"Generating challenge suggestion for topic: '{topic}' (language: {language})")
        
        try:
            # Call OpenAI service to generate the suggestion
            suggestion = await self.openai_service.generate_challenge_suggestion(
                topic=topic,
                language=language
            )
            
            # Validate the response structure
            self._validate_suggestion(suggestion)
            
            logger.info(
                f"Successfully generated challenge: '{suggestion.get('title')}' "
                f"with {len(suggestion.get('testCases', []))} test cases"
            )
            
            return suggestion
            
        except ValueError as e:
            # Re-raise validation errors
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate challenge suggestion: {str(e)}")
            raise Exception(f"Failed to generate challenge: {str(e)}")
    
    def _validate_suggestion(self, suggestion: Dict[str, Any]) -> None:
        """
        Validate that the suggestion has all required fields.
        
        Args:
            suggestion: The generated suggestion dictionary
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = [
            "title", "description", "difficulty", "tags",
            "examples", "testCases", "limits"
        ]
        
        for field in required_fields:
            if field not in suggestion:
                raise ValueError(f"Generated suggestion is missing required field: {field}")
        
        # Validate difficulty
        valid_difficulties = ["Easy", "Medium", "Hard"]
        if suggestion["difficulty"] not in valid_difficulties:
            raise ValueError(
                f"Invalid difficulty '{suggestion['difficulty']}'. "
                f"Must be one of: {', '.join(valid_difficulties)}"
            )
        
        # Validate test cases
        test_cases = suggestion.get("testCases", [])
        if len(test_cases) < 5:
            raise ValueError(
                f"Generated suggestion must have at least 5 test cases, got {len(test_cases)}"
            )
        
        # Validate that at least first 2 test cases are visible
        public_test_cases = [tc for tc in test_cases if not tc.get("is_hidden", True)]
        if len(public_test_cases) < 2:
            logger.warning(
                f"Generated suggestion has only {len(public_test_cases)} public test cases. "
                "Recommended to have at least 2 public cases."
            )
        
        # Validate examples
        examples = suggestion.get("examples", [])
        if len(examples) < 1:
            raise ValueError("Generated suggestion must have at least 1 example")
        
        # Validate limits
        limits = suggestion.get("limits", {})
        if "timeLimitMs" not in limits or "memoryLimitMb" not in limits:
            raise ValueError("Generated suggestion must include time and memory limits")
        
        logger.debug("Suggestion validation passed")
