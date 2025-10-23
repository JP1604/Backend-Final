from enum import Enum
from datetime import datetime
from typing import Optional, List


class ChallengeDifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class ChallengeStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Challenge:
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        difficulty: ChallengeDifficulty,
        tags: List[str],
        time_limit: int,  # in milliseconds
        memory_limit: int,  # in MB
        status: ChallengeStatus,
        created_by: str,  # User ID
        course_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.tags = tags
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.status = status
        self.created_by = created_by
        self.course_id = course_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def is_published(self) -> bool:
        return self.status == ChallengeStatus.PUBLISHED

    def is_draft(self) -> bool:
        return self.status == ChallengeStatus.DRAFT

    def is_archived(self) -> bool:
        return self.status == ChallengeStatus.ARCHIVED

    def can_be_viewed_by(self, user_role: str) -> bool:
        return self.is_published() or user_role in ["ADMIN", "PROFESSOR"]

    def can_be_edited_by(self, user_id: str, user_role: str) -> bool:
        return (self.created_by == user_id) or user_role == "ADMIN"
