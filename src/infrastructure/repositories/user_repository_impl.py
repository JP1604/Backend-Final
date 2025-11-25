from typing import Optional, List
from sqlalchemy.orm import Session
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from infrastructure.persistence.models import UserModel
from datetime import datetime


class UserRepositoryImpl(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def find_by_id(self, user_id: str) -> Optional[User]:
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(user_model) if user_model else None

    async def find_by_email(self, email: str) -> Optional[User]:
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(user_model) if user_model else None

    async def save(self, user: User) -> User:
        user_model = self._to_model(user)
        self.db.add(user_model)
        self.db.commit()
        self.db.refresh(user_model)
        return self._to_domain(user_model)

    async def update(self, user: User) -> User:
        user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if user_model:
            user_model.email = user.email
            user_model.password = user.password
            user_model.first_name = user.first_name
            user_model.last_name = user.last_name
            user_model.role = user.role
            user_model.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user_model)
            return self._to_domain(user_model)
        return user

    async def delete(self, user_id: str) -> None:
        self.db.query(UserModel).filter(UserModel.id == user_id).delete()
        self.db.commit()

    async def find_all(self) -> List[User]:
        user_models = self.db.query(UserModel).all()
        return [self._to_domain(user_model) for user_model in user_models]

    def _to_domain(self, user_model: UserModel) -> User:
        return User(
            id=str(user_model.id),
            email=user_model.email,
            password=user_model.password,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            role=user_model.role,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at
        )

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
