from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def find_all(self) -> List[User]:
        pass
