from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.challenge import Challenge


class TestCase:
    """Test case entity for challenges"""
    def __init__(
        self,
        id: str,
        challenge_id: str,
        input: str,
        expected_output: str,
        is_hidden: bool = False,
        order_index: int = 0
    ):
        self.id = id
        self.challenge_id = challenge_id
        self.input = input
        self.expected_output = expected_output
        self.is_hidden = is_hidden
        self.order_index = order_index


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
    
    @abstractmethod
    async def get_test_cases(self, challenge_id: str) -> List[TestCase]:
        """Get all test cases for a challenge"""
        pass
