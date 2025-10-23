from pydantic import BaseModel
from typing import List, Optional
from ...domain.entities.challenge import ChallengeDifficulty


class CreateChallengeRequest(BaseModel):
    title: str
    description: str
    difficulty: ChallengeDifficulty
    tags: List[str]
    time_limit: int
    memory_limit: int
    course_id: Optional[str] = None


class ChallengeResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: ChallengeDifficulty
    tags: List[str]
    time_limit: int
    memory_limit: int
    status: str
    created_by: str
    course_id: Optional[str]
    created_at: str
    updated_at: str