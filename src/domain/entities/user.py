from enum import Enum
from datetime import datetime
from typing import Optional


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    PROFESSOR = "PROFESSOR"
    ADMIN = "ADMIN"


class User:
    def __init__(
        self,
        id: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_professor(self) -> bool:
        return self.role == UserRole.PROFESSOR

    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    def can_create_challenges(self) -> bool:
        return self.is_admin() or self.is_professor()

    def can_view_all_challenges(self) -> bool:
        return self.is_admin() or self.is_professor()
