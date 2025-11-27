"""
Exam Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from domain.entities.exam import ExamStatus


class CreateExamRequest(BaseModel):
    """Request to create a new exam"""
    course_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    duration_minutes: int = Field(..., gt=0, description="Maximum duration per student in minutes")
    max_attempts: int = Field(default=1, ge=1, description="Maximum attempts per student")
    passing_score: Optional[int] = Field(None, ge=0, le=100, description="Minimum score to pass (0-100)")
    status: ExamStatus = ExamStatus.DRAFT


class UpdateExamRequest(BaseModel):
    """Request to update exam details"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    max_attempts: Optional[int] = Field(None, ge=1)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[ExamStatus] = None


class ExamResponse(BaseModel):
    """Response with exam details"""
    id: str
    course_id: str
    title: str
    description: Optional[str]
    status: ExamStatus
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    max_attempts: int
    passing_score: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class ExamAttemptResponse(BaseModel):
    """Response with exam attempt details"""
    id: str
    exam_id: str
    user_id: str
    score: int
    passed: bool
    started_at: datetime
    submitted_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class ExamResultsResponse(BaseModel):
    """Response with exam results summary"""
    exam_id: str
    exam_title: str
    total_attempts: int
    passed_attempts: int
    average_score: float
    attempts: List[ExamAttemptResponse]
    
    class Config:
        from_attributes = True


class AssignChallengeToExamRequest(BaseModel):
    """Request to assign a challenge to an exam"""
    challenge_id: str
    points: int = Field(default=100, ge=0, description="Points this challenge is worth")
    order_index: int = Field(default=0, ge=0, description="Display order in the exam")


class ExamChallengeResponse(BaseModel):
    """Response with exam challenge details"""
    challenge_id: str
    title: str
    description: str
    difficulty: str
    points: int
    order_index: int
    
    class Config:
        from_attributes = True
