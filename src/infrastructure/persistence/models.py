from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Enum as SQLEnum, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.persistence.database import Base
from domain.entities.user import UserRole
from domain.entities.challenge import ChallengeDifficulty, ChallengeStatus
from domain.entities.submission import SubmissionStatus, ProgrammingLanguage
from domain.entities.course import CourseStatus
from domain.entities.exam import ExamStatus


class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChallengeModel(Base):
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)  # VARCHAR en BD, no ENUM
    tags = Column(ARRAY(String), nullable=False)
    time_limit = Column(Integer, nullable=False)
    memory_limit = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='draft')  # VARCHAR en BD, no ENUM
    language = Column(SQLEnum(ProgrammingLanguage), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SubmissionModel(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    challenge_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    language = Column(SQLEnum(ProgrammingLanguage), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(SQLEnum(SubmissionStatus), nullable=False, default=SubmissionStatus.QUEUED)
    score = Column(Integer, nullable=False, default=0)
    time_ms_total = Column(Integer, nullable=False, default=0)
    cases = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TestCaseModel(Base):
    __tablename__ = "test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    challenge_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    input = Column(Text, nullable=True)  # Optional - only expected_output is required
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# Association table for many-to-many relationship between courses and students
course_students = Table(
    'course_students',
    Base.metadata,
    Column('course_id', UUID(as_uuid=True), ForeignKey('courses.id'), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('enrolled_at', DateTime(timezone=True), server_default=func.now())
)


# Association table for many-to-many relationship between courses and challenges
course_challenges = Table(
    'course_challenges',
    Base.metadata,
    Column('course_id', UUID(as_uuid=True), ForeignKey('courses.id'), primary_key=True),
    Column('challenge_id', UUID(as_uuid=True), ForeignKey('challenges.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('order_index', Integer, nullable=False, default=0)
)


# Association table for many-to-many relationship between exams and challenges
exam_challenges = Table(
    'exam_challenges',
    Base.metadata,
    Column('exam_id', UUID(as_uuid=True), ForeignKey('exams.id'), primary_key=True),
    Column('challenge_id', UUID(as_uuid=True), ForeignKey('challenges.id'), primary_key=True),
    Column('points', Integer, nullable=False, default=100),  # Points for this challenge in the exam
    Column('order_index', Integer, nullable=False, default=0)
)


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    # Use String instead of Enum to store the enum value (lowercase string)
    status = Column(String(20), nullable=False, default=CourseStatus.DRAFT.value)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExamModel(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=ExamStatus.DRAFT.value)
    
    # Time constraints
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # Max duration per student
    
    # Attempt constraints
    max_attempts = Column(Integer, nullable=False, default=1)
    
    # Scoring
    passing_score = Column(Integer, nullable=True)  # Minimum score to pass (0-100)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)


class ExamAttemptModel(Base):
    """Track student attempts on exams"""
    __tablename__ = "exam_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    score = Column(Integer, nullable=False, default=0)
    passed = Column(Boolean, nullable=False, default=False)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)  # Currently taking the exam
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


