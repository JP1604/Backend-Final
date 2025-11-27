"""
Course Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from domain.entities.course import CourseStatus


class CreateCourseRequest(BaseModel):
    """Request to create a new course"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[CourseStatus] = CourseStatus.DRAFT


class UpdateCourseRequest(BaseModel):
    """Request to update course details"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[CourseStatus] = None


class EnrollStudentRequest(BaseModel):
    """Request to enroll a student"""
    student_id: str


class AssignChallengeRequest(BaseModel):
    """Request to assign a challenge to a course"""
    challenge_id: str
    order_index: int = 0


class CourseResponse(BaseModel):
    """Response with course details"""
    id: str
    name: str
    description: Optional[str]
    teacher_id: str
    status: CourseStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CourseWithStatsResponse(BaseModel):
    """Response with course details and statistics"""
    id: str
    name: str
    description: Optional[str]
    teacher_id: str
    status: CourseStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    student_count: int = 0
    challenge_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentEnrollmentResponse(BaseModel):
    """Response for student enrollment"""
    course_id: str
    student_id: str
    enrolled_at: datetime
    success: bool = True
    message: str = "Student enrolled successfully"


class ChallengeAssignmentResponse(BaseModel):
    """Response for challenge assignment"""
    course_id: str
    challenge_id: str
    assigned_at: datetime
    order_index: int
    success: bool = True
    message: str = "Challenge assigned successfully"


class ExamResponse(BaseModel):
    """Response with exam details"""
    id: str
    course_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    max_attempts: int
    passing_score: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentDetailResponse(BaseModel):
    """Response with detailed student information"""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    enrolled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExamScoreResponse(BaseModel):
    """Response with exam score information"""
    exam_id: str
    exam_title: str
    user_id: str
    attempt_id: str
    score: int
    passed: bool
    started_at: datetime
    submitted_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

