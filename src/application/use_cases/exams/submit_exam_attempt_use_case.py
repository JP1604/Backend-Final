"""Finalize an exam attempt by calculating the score from submissions.

The calculation here uses the best submission per challenge made by the
student during the attempt window (started_at .. now). Each exam challenge
has assigned points stored in `exam_challenges`.
"""
import logging
from datetime import datetime
from typing import List

from infrastructure.persistence.models import exam_challenges

logger = logging.getLogger(__name__)


class SubmitExamAttemptUseCase:
    def __init__(self, exam_repository, submission_repository, db_session):
        self.exam_repository = exam_repository
        self.submission_repository = submission_repository
        self.db = db_session

    async def execute(self, attempt_id: str) -> dict:
        """Finalize the attempt: compute score and mark attempt submitted.

        Returns finalized attempt dict with score and passed boolean.
        """
        # Get attempt
        attempt = await self.exam_repository.get_attempt_by_id(attempt_id)
        if not attempt:
            raise ValueError("Exam attempt not found")

        # Get exam id and started_at
        exam_id = attempt['exam_id']
        started_at = attempt['started_at']

        # Get exam challenges with points
        rows = self.db.execute(
            exam_challenges.select().where(exam_challenges.c.exam_id == exam_id)
        ).fetchall()
        challenge_points = [(str(r.challenge_id), int(r.points or 0)) for r in rows]

        if not challenge_points:
            logger.warning(f"[NO_CHALLENGES] Exam {exam_id} has no challenges assigned")
            # Finalize with 0 score if no challenges
            finalized = await self.exam_repository.finalize_attempt(attempt_id, 0, False)
            return finalized

        total_points = 0
        earned_points = 0
        now = datetime.utcnow()

        for ch_id, points in challenge_points:
            total_points += points
            # Find best submission by this user for this challenge between started_at and now
            subs = await self.submission_repository.find_by_user_and_challenge(attempt['user_id'], ch_id)
            # Filter by timestamps within attempt window
            subs_in_attempt = [
                s for s in subs 
                if getattr(s, 'created_at', None) 
                and s.created_at >= started_at 
                and s.created_at <= now
            ]
            
            best = None
            for s in subs_in_attempt:
                # Only consider completed submissions
                if not s.is_completed():
                    continue
                if best is None:
                    best = s
                else:
                    # Prefer higher score, then faster time
                    if s.score > best.score:
                        best = s
                    elif s.score == best.score and s.time_ms_total < best.time_ms_total:
                        best = s

            if best:
                # best.score is 0-100, scale to points
                score_percentage = int(getattr(best, 'score', 0) or 0)
                earned_points += round(points * (score_percentage / 100.0))
                logger.debug(
                    f"[CHALLENGE_SCORE] Challenge {ch_id}: {score_percentage}% = "
                    f"{round(points * (score_percentage / 100.0))}/{points} points"
                )

        # Compute percentage and pass/fail
        percent = round((earned_points / total_points) * 100) if total_points > 0 else 0

        passed = False
        # Retrieve passing_score from exam
        exam_dict = await self.exam_repository.get_exam_dict_by_id(exam_id)
        if exam_dict and exam_dict.get('passing_score') is not None:
            passing_score = int(exam_dict.get('passing_score') or 0)
            passed = percent >= passing_score
            logger.info(
                f"[EXAM_SCORE] Exam {exam_id}: {percent}% "
                f"(passing: {passing_score}%, passed: {passed})"
            )
        else:
            # No passing score requirement, consider any score as passed
            passed = percent > 0
            logger.info(f"[EXAM_SCORE] Exam {exam_id}: {percent}% (no passing requirement)")

        # Finalize attempt
        finalized = await self.exam_repository.finalize_attempt(attempt_id, int(percent), passed)

        return finalized
