from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from uuid import UUID
from domain.entities.challenge import ChallengeDifficulty


class CreateChallengeRequest(BaseModel):
    title: str
    description: str
    difficulty: ChallengeDifficulty
    tags: List[str]
    time_limit: int
    memory_limit: int
    course_id: Optional[str] = Field(None, description="UUID válido del curso o null")
    
    @field_validator('course_id')
    @classmethod
    def validate_course_id(cls, v):
        if v is None or v == "":
            return None
        try:
            # Validar que sea un UUID válido
            UUID(v)
            return v
        except ValueError:
            raise ValueError('course_id debe ser un UUID válido o null')


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