"""Start an exam attempt for a student."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StartExamAttemptUseCase:
    def __init__(self, exam_repository, course_repository):
        self.exam_repository = exam_repository
        self.course_repository = course_repository

    async def execute(self, exam_id: str, user_id: str) -> dict:
        """Create a new exam attempt after validating constraints.

        Returns the created attempt info.
        """
        try:
            from uuid import UUID
            # Normalize user_id to string for consistent comparison
            user_id_str = str(user_id).lower().strip()
            
            # Verify exam exists
            exam = await self.exam_repository.get_exam_by_id(exam_id)
            if not exam:
                raise ValueError("Exam not found")

            # Check if student can start
            # Count current attempts
            attempts = await self.exam_repository.get_attempts_by_exam_id(exam_id)
            # Normalize user_id for comparison
            user_attempts = [a for a in attempts if str(a["user_id"]).lower().strip() == user_id_str]
            current_attempts = len(user_attempts)
            
            can_start, reason = exam.can_student_start(current_attempts)
            if not can_start:
                raise ValueError(reason)

            # Verify user is enrolled in course
            course_students = await self.course_repository.get_students(exam.course_id)
            # Normalize all student IDs for comparison
            course_students_normalized = [str(sid).lower().strip() for sid in course_students]
            if user_id_str not in course_students_normalized:
                logger.warning(f"[ENROLLMENT_CHECK] User {user_id} not found in course {exam.course_id}. Enrolled students: {course_students_normalized}")
                raise ValueError("User not enrolled in the exam course")

            # Create attempt
            attempt = await self.exam_repository.create_attempt(exam_id, user_id)
            logger.info(f"Created exam attempt {attempt['id']} for user {user_id} exam {exam_id}")
            return attempt
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[START_EXAM_ATTEMPT_ERROR] Unexpected error: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to start exam attempt: {str(e)}")
