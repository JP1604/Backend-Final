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

        total_points = 0
        earned_points = 0

        for ch_id, points in challenge_points:
            total_points += points
            # Find best submission by this user for this challenge between started_at and now
            subs = await self.submission_repository.find_by_user_and_challenge(attempt['user_id'], ch_id)
            # Filter by timestamps within attempt
            subs_in_attempt = [s for s in subs if getattr(s, 'created_at', None) and s.created_at >= started_at]
            best = None
            for s in subs_in_attempt:
                if not getattr(s, 'is_completed', lambda: True)():
                    continue
                if best is None:
                    best = s
                else:
                    if s.score > best.score:
                        best = s
                    elif s.score == best.score and s.time_ms_total < best.time_ms_total:
                        best = s

            if best:
                # assume best.score is 0-100 - scale to points
                earned_points += round(points * (int(getattr(best, 'score', 0) or 0) / 100.0))

        # Compute percentage and pass/fail
        percent = round((earned_points / total_points) * 100) if total_points > 0 else 0

        passed = False
        # retrieve passing_score from exam
        exam = await self.exam_repository.get_exam_by_id(exam_id)
        if exam and exam.get('passing_score') is not None:
            passed = percent >= int(exam.get('passing_score') or 0)

        # Finalize attempt
        finalized = await self.exam_repository.finalize_attempt(attempt_id, int(percent), passed)

        # Schedule leaderboard recalculation (best-effort)
        try:
            import asyncio
            from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
            from application.use_cases.leaderboards.recalculate_exam_leaderboard_use_case import RecalculateExamLeaderboardUseCase

            db = self.db
            user_repo = UserRepositoryImpl(db)
            recalc_uc = RecalculateExamLeaderboardUseCase(self.exam_repository, user_repo)
            asyncio.create_task(recalc_uc.execute(exam_id))
            logger.info(f"Scheduled exam leaderboard recalculation for exam {exam_id}")
        except Exception:
            logger.debug("Failed to schedule exam leaderboard recalculation")

        return finalized
