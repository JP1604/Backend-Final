from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.submission import Submission


class SubmissionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, submission_id: str) -> Optional[Submission]:
        pass

    @abstractmethod
    async def save(self, submission: Submission) -> Submission:
        pass

    @abstractmethod
    async def update(self, submission: Submission) -> Submission:
        pass

    @abstractmethod
    async def delete(self, submission_id: str) -> None:
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Submission]:
        pass

    @abstractmethod
    async def find_by_challenge_id(self, challenge_id: str) -> List[Submission]:
        pass

    @abstractmethod
    async def find_by_user_and_challenge(self, user_id: str, challenge_id: str) -> List[Submission]:
        pass
