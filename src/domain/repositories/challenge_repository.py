from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.challenge import Challenge


class ChallengeRepository(ABC):
    @abstractmethod
    async def find_by_id(self, challenge_id: str) -> Optional[Challenge]:
        pass

    @abstractmethod
    async def save(self, challenge: Challenge) -> Challenge:
        pass

    @abstractmethod
    async def update(self, challenge: Challenge) -> Challenge:
        pass

    @abstractmethod
    async def delete(self, challenge_id: str) -> None:
        pass

    @abstractmethod
    async def find_all(self, filters: dict = None) -> List[Challenge]:
        pass
