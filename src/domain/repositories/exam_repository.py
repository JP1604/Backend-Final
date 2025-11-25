from abc import ABC, abstractmethod
from typing import List, Optional


class ExamRepository(ABC):
    @abstractmethod
    async def get_attempts_by_exam_id(self, exam_id: str) -> List[dict]:
        """Return list of exam attempts as dicts with keys: user_id, score, started_at, submitted_at, passed"""
        pass
